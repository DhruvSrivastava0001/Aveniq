"""Grounded customer-intelligence endpoints for ChurnIQ.

Answers and investigations are computed from approved, deterministic analytics.
No unrestricted SQL, external LLM calls, or invented model explanations are used.
"""
from __future__ import annotations

import io
import os
import json
import asyncio
import logging
from pathlib import Path
import requests
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.analytics.data_loader import load_customer_data

router = APIRouter(prefix="/api/intelligence", tags=["Customer Intelligence"])
_alert_lock = Lock()
_RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
_SETTINGS_PATH = _RUNTIME_DIR / "alert_settings.json"
_HISTORY_PATH = _RUNTIME_DIR / "alert_history.jsonl"
_REPORT_DIR = _RUNTIME_DIR / "reports"
_LOG = logging.getLogger("churniq.monitoring")
_DEFAULT_ALERT_SETTINGS: dict[str, Any] = {
    "churn_rate_threshold": 25.0,
    "minimum_segment_size": 30,
    "enabled": True,
}


def _load_alert_settings() -> dict[str, Any]:
    try:
        with _SETTINGS_PATH.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        return {**_DEFAULT_ALERT_SETTINGS, **loaded}
    except (OSError, ValueError, TypeError):
        return dict(_DEFAULT_ALERT_SETTINGS)


_alert_settings: dict[str, Any] = _load_alert_settings()


def _persist_alert_settings() -> None:
    _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    temporary = _SETTINGS_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(_alert_settings, handle, indent=2)
    temporary.replace(_SETTINGS_PATH)


def _append_history(entry: dict[str, Any]) -> None:
    _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with _HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def _evaluate_snapshot(df: pd.DataFrame, settings: dict[str, Any]) -> dict[str, Any]:
    summary = _summary(df)
    alerts = []
    if settings["enabled"] and summary["churn_rate"] >= settings["churn_rate_threshold"]:
        alerts.append({"severity": "warning", "metric": "overall_churn_rate", "actual": summary["churn_rate"], "threshold": settings["churn_rate_threshold"], "message": f"Observed churn rate {summary['churn_rate']:.2f}% meets or exceeds the configured {settings['churn_rate_threshold']:.2f}% threshold."})
    small_segments = []
    for column in ("telecom_partner", "state"):
        for row in _group_stats(df, column):
            if row["customers"] < settings["minimum_segment_size"]:
                small_segments.append({"segment_type": column, "segment": row[column], "customers": row["customers"]})
    if small_segments:
        alerts.append({"severity": "info", "metric": "small_segments", "message": f"{len(small_segments)} partner/state segments are below the configured sample minimum.", "segments": small_segments[:25]})
    return {"evaluated_at": datetime.now(timezone.utc).isoformat(), "summary": summary, "settings": settings, "alerts": alerts}


def _write_aggregate_report(snapshot: dict[str, Any], df: pd.DataFrame) -> None:
    """Write a low-sensitivity aggregate snapshot, never raw customer records."""
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    partner_rates = _group_stats(df, "telecom_partner")
    state_rates = _group_stats(df, "state")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": snapshot["summary"],
        "top_partner_rates": partner_rates[:5],
        "top_state_rates": state_rates[:5],
        "alert_count": len(snapshot["alerts"]),
    }
    filename = _REPORT_DIR / f"aggregate_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    filename.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _run_scheduled_monitoring(write_report: bool = False) -> dict[str, Any]:
    df = _data()
    with _alert_lock:
        settings = dict(_alert_settings)
    snapshot = _evaluate_snapshot(df, settings)
    snapshot["source"] = "scheduled"
    _append_history(snapshot)
    for alert in snapshot["alerts"]:
        _LOG.warning("ChurnIQ scheduled alert: %s", alert)
    if write_report and os.getenv("CHURNIQ_AUTO_REPORT_ENABLED", "true").strip().lower() in {"1", "true", "yes"}:
        _write_aggregate_report(snapshot, df)
    return snapshot


async def monitoring_loop() -> None:
    """Periodic aggregate checks; configure cadence via environment variables."""
    interval = max(60, int(os.getenv("CHURNIQ_MONITOR_INTERVAL_SECONDS", "3600")))
    report_interval = max(3600, int(os.getenv("CHURNIQ_AUTO_REPORT_INTERVAL_SECONDS", "86400")))
    last_report = 0.0
    while True:
        await asyncio.sleep(interval)
        try:
            should_report = datetime.now(timezone.utc).timestamp() - last_report >= report_interval
            snapshot = await asyncio.to_thread(_run_scheduled_monitoring, should_report)
            if should_report:
                _LOG.info("ChurnIQ aggregate report generated: %s", snapshot.get("summary"))
                last_report = datetime.now(timezone.utc).timestamp()
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOG.exception("ChurnIQ scheduled monitoring failed; it will retry next interval.")


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class InvestigationRequest(BaseModel):
    telecom_partner: str | None = None
    state: str | None = None
    focus: str = Field(default="churn", max_length=80)


class AlertSettings(BaseModel):
    churn_rate_threshold: float = Field(default=25.0, ge=0, le=100)
    minimum_segment_size: int = Field(default=30, ge=1, le=1000000)
    enabled: bool = True





def _normalize_partner_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize telecom partner aliases for consistent analytics."""
    df = df.copy()

    if "telecom_partner" not in df.columns:
        return df

    aliases = {
        "jio": "Reliance Jio",
        "reliance jio": "Reliance Jio",
        "vodafone": "Vi",
        "vi": "Vi",
    }

    def normalize(value):
        if pd.isna(value):
            return value

        cleaned = str(value).strip()

        if not cleaned:
            return "Unknown"

        return aliases.get(cleaned.casefold(), cleaned)

    df["telecom_partner"] = df["telecom_partner"].map(normalize)

    return df












def _data() -> pd.DataFrame:
    try:
        df = load_customer_data()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Customer data is unavailable. Start Spring Boot and MySQL, then retry.",
        ) from exc
    if df.empty:
        raise HTTPException(status_code=503, detail="No customer records are available yet.")
    # Normalize common field names without modifying the shared cache.
    mapping = {
        "customerId": "customer_id", "telecomPartner": "telecom_partner",
        "dateOfRegistration": "date_of_registration", "numDependents": "num_dependents",
        "estimatedSalary": "estimated_salary", "callsMade": "calls_made",
        "smsSent": "sms_sent", "dataUsed": "data_used",
    }
    df = df.rename(columns=mapping).copy()
    df = _normalize_partner_names(df)
    if "churn" not in df.columns:
        raise HTTPException(status_code=500, detail="The customer dataset has no churn field.")
    df["churn"] = pd.to_numeric(df["churn"], errors="coerce")
    df = df[df["churn"].isin([0, 1])].copy()
    df["churn"] = df["churn"].astype(int)
    return df


def _summary(df: pd.DataFrame) -> dict[str, Any]:
    n = len(df)
    churned = int(df["churn"].sum()) if n else 0
    return {
        "total_customers": n,
        "churned_customers": churned,
        "retained_customers": n - churned,
        "churn_rate": round(churned * 100 / n, 2) if n else 0.0,
    }


def _group_stats(df: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    if column not in df.columns or df.empty:
        return []
    values = df.copy()
    values[column] = values[column].fillna("Unknown").astype(str).str.strip()
    values.loc[values[column].eq(""), column] = "Unknown"
    result = values.groupby(column, dropna=False).agg(
        customers=("churn", "size"), churned=("churn", "sum")
    ).reset_index()
    result["churn_rate"] = (result["churned"] / result["customers"] * 100).round(2)
    return result.sort_values(["churn_rate", "customers"], ascending=[False, False]).to_dict("records")


def _filtered(
    df: pd.DataFrame,
    partner: str | None = None,
    state: str | None = None,
) -> pd.DataFrame:
    df = _normalize_partner_names(df)

    if partner and "telecom_partner" in df.columns:
        normalized_partner = _normalize_partner_names(
            pd.DataFrame({"telecom_partner": [partner]})
        )["telecom_partner"].iloc[0]

        df = df[
            df["telecom_partner"].astype(str).str.casefold()
            == str(normalized_partner).casefold()
        ]

    if state and "state" in df.columns:
        df = df[
            df["state"].astype(str).str.casefold()
            == state.strip().casefold()
        ]

    return df.copy()


@router.get("/overview")
def intelligence_overview():
    df = _data()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": _summary(df),
        "by_partner": _group_stats(df, "telecom_partner"),
        "by_state": _group_stats(df, "state"),
        "by_city": _group_stats(df, "city"),
        "by_gender": _group_stats(df, "gender"),
        "data_source": "Spring Boot / MySQL",
        "model_warning": "Current churn model ranking performance is near random (ROC-AUC about 0.50); this page uses observed labels and descriptive analytics, not model predictions.",
    }


def _is_customer_analytics_question(question: str) -> bool:
    """Detect requests for this app's metrics without hijacking general questions."""
    q = question.casefold()
    explicit_data_context = any(term in q for term in (
        "our data", "our customers", "in the dataset", "current dataset",
        "customer records", "recorded customers", "observed churn",
        "from the data", "in churniq", "this dataset",
    ))
    segment_terms = ("partner", "provider", "telecom", "state", "city", "gender")
    segment_question = any(term in q for term in segment_terms) and any(
        term in q for term in ("highest", "lowest", "compare", "comparison", "breakdown", "by ", "rate", "customers", "customer count")
    )
    count_question = any(term in q for term in (
        "how many customer", "customer count", "number of customer", "count of customer",
        "how many churned", "how many retained",
    ))
    overall_metric = any(term in q for term in (
        "overall churn rate", "current churn rate", "observed churn rate",
        "our churn rate", "overall churn", "churn rate in the dataset",
    ))
    report_question = any(term in q for term in ("customer report", "dataset summary", "our customer summary", "business insight report"))
    return explicit_data_context or segment_question or count_question or overall_metric or report_question


def _ask_language_model(question: str, aggregate_context: dict[str, Any] | None = None,
                        reference_answer: str | None = None) -> str | None:
    """Call the configured OpenAI-compatible chat endpoint, never with raw customer rows."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    is_analytics = aggregate_context is not None
    system_prompt = (
        "You are ChurnIQ, a practical, friendly general-purpose assistant inside a customer analytics app. "
        "Answer general knowledge, programming, writing, study, and productivity questions clearly. "
        "For questions about the app's customer data, use only the supplied aggregate JSON and reference answer; "
        "never invent customer counts or segment values, and never infer causation from observed churn. "
        "If the aggregates cannot answer a data question, explain what is missing. Distinguish general knowledge "
        "from dataset findings. Do not reveal or request secrets."
    )
    user_content = f"Question: {question}"
    if is_analytics:
        user_content += (
            f"\nApproved aggregate data: {json.dumps(aggregate_context, default=str)}"
            f"\nDeterministic reference answer: {reference_answer or 'No deterministic answer available.'}"
        )
    try:
        response = requests.post(
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            },
            timeout=25,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content or None
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        _LOG.warning("Configured language model failed; using the local fallback.")
        return None


@router.post("/chat")
def chat(request: ChatRequest):
    """Answer general questions with the configured LLM and customer questions from live aggregates."""
    question = request.question.strip()
    if not _is_customer_analytics_question(question):
        llm_answer = _ask_language_model(question)
        if llm_answer:
            return {
                "answer": llm_answer,
                "sources": ["Configured language model; no customer records were sent"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "grounded": False,
                "mode": "general_llm",
            }
        return {
            "answer": (
                "I can help with general questions, coding, writing, study, and productivity when a language-model "
                "provider is configured. To enable that, set OPENAI_API_KEY (and optionally OPENAI_MODEL) in the "
                "FastAPI backend environment, then restart the API. Customer-data analytics continue to work "
                "without an API key. For now, try asking about observed churn, customer counts, or partner/state comparisons."
            ),
            "sources": ["Local configuration guidance"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "grounded": False,
            "mode": "general_llm_unconfigured",
        }

    df = _data()
    q = question.casefold()
    summary = _summary(df)
    partner_stats = _group_stats(df, "telecom_partner")
    state_stats = _group_stats(df, "state")
    city_stats = _group_stats(df, "city")
    answer: str
    sources: list[str] = ["Current customer records in MySQL", "Deterministic churn-rate calculations"]
    lowest = any(t in q for t in ["lowest", "least", "minimum", "smallest"])
    highest = any(t in q for t in ["highest", "most", "maximum", "largest", "top"])

    if any(term in q for term in ["total customer", "how many customer", "customer count", "number of customer", "count of customer"]):
        if any(term in q for term in ["churned", "churn customer", "left"]):
            answer = f"{summary['churned_customers']:,} of {summary['total_customers']:,} valid customer records are labelled churned."
        elif any(term in q for term in ["retained", "stay", "active"]):
            answer = f"{summary['retained_customers']:,} of {summary['total_customers']:,} valid customer records are labelled retained."
        else:
            answer = f"There are {summary['total_customers']:,} customers in the current dataset: {summary['churned_customers']:,} labelled churned and {summary['retained_customers']:,} labelled retained."
    elif any(term in q for term in ["churn rate", "overall churn", "percentage churn", "churn percentage"]) and not any(term in q for term in ["partner", "provider", "telecom", "state", "city"]):
        answer = f"The observed churn rate is {summary['churn_rate']:.2f}% ({summary['churned_customers']:,} of {summary['total_customers']:,} valid customer records). This describes existing labels; it is not a forecast."
    elif any(term in q for term in ["partner", "provider", "telecom"]):
        if not partner_stats:
            answer = "Partner-level data is not available in the current customer records."
        else:
            row = (min if lowest and not highest else max)(partner_stats, key=lambda x: x["churn_rate"])
            direction = "lowest" if lowest and not highest else "highest"
            answer = f"{row['telecom_partner']} has the {direction} observed churn rate at {row['churn_rate']:.2f}% across {row['customers']:,} customers ({row['churned']:,} labelled churned). Partner rates are descriptive and may not indicate a causal effect."
    elif "state" in q:
        if not state_stats:
            answer = "State-level data is not available in the current customer records."
        else:
            row = (min if lowest and not highest else max)(state_stats, key=lambda x: x["churn_rate"])
            direction = "lowest" if lowest and not highest else "highest"
            answer = f"{row['state']} has the {direction} observed churn rate at {row['churn_rate']:.2f}% ({row['churned']:,} of {row['customers']:,} customers). Treat this as a descriptive comparison, not a causal conclusion."
    elif "city" in q:
        if not city_stats:
            answer = "City-level data is not available in the current customer records."
        else:
            row = (min if lowest and not highest else max)(city_stats, key=lambda x: x["churn_rate"])
            direction = "lowest" if lowest and not highest else "highest"
            answer = f"{row['city']} has the {direction} observed city-level churn rate at {row['churn_rate']:.2f}% ({row['churned']:,} of {row['customers']:,} customers)."
    elif any(t in q for t in ["gender", "male", "female"]):
        stats = _group_stats(df, "gender")
        answer = "Observed churn by gender: " + ("; ".join(f"{r.get('gender', 'Unknown')}: {r['churn_rate']:.2f}% ({r['customers']:,} customers)" for r in stats) if stats else "not available") + ". These differences are descriptive and should not be used to make unfair individual decisions."
    elif any(t in q for t in ["report", "summary", "overview", "insight"]):
        top_partner = max(partner_stats, key=lambda x: x["churn_rate"]) if partner_stats else None
        answer = f"Current summary: {summary['total_customers']:,} customers; {summary['churned_customers']:,} labelled churned; observed churn rate {summary['churn_rate']:.2f}%." + (f" Highest partner rate: {top_partner['telecom_partner']} at {top_partner['churn_rate']:.2f}%." if top_partner else "") + " Use the Reports tab to export the current dataset."
    else:
        answer = "I can answer questions about customer counts, observed churn rates, churned/retained totals, partner/state/city comparisons, gender breakdowns, and report summaries. For broader questions, configure OPENAI_API_KEY to enable general-purpose answers."
        sources = ["Supported question types and backend configuration"]

    safe_context = {
        "summary": summary,
        "partner_rates": partner_stats,
        "state_rates": state_stats,
        "city_rates": city_stats,
        "gender_rates": _group_stats(df, "gender"),
    }
    llm_answer = _ask_language_model(question, safe_context, answer)
    mode = "deterministic"
    if llm_answer:
        answer = llm_answer
        mode = "analytics_llm_with_aggregate_context"
    elif os.getenv("OPENAI_API_KEY", "").strip():
        mode = "deterministic_fallback_provider_unavailable"

    return {
        "answer": answer,
        "sources": sources,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "grounded": True,
        "mode": mode,
    }


@router.post("/investigate")
def investigate(request: InvestigationRequest):
    df = _filtered(_data(), request.telecom_partner, request.state)
    if df.empty:
        raise HTTPException(status_code=404, detail="No customers match the selected filters.")
    summary = _summary(df)
    minimum = int(_alert_settings["minimum_segment_size"])
    warnings = []
    if len(df) < minimum:
        warnings.append(f"Small sample: {len(df)} customers; configured minimum is {minimum}.")
    partner = _group_stats(df, "telecom_partner")
    state = _group_stats(df, "state")
    usage = {}
    for col in ("calls_made", "sms_sent", "data_used", "age", "estimated_salary"):
        if col in df.columns:
            values = pd.to_numeric(df[col], errors="coerce").dropna()
            if not values.empty:
                usage[col] = {"mean": round(float(values.mean()), 2), "median": round(float(values.median()), 2), "available": int(values.size)}
    recommendations = [
        "Validate the operational definition and observation window for the churn label before treating this as a retention forecast.",
        "Compare the segment with the overall population and investigate customer feedback or service-quality data before assigning a cause.",
        "Evaluate a retention intervention with a measured control group before claiming that it reduces churn.",
    ]
    if summary["churn_rate"] >= float(_alert_settings["churn_rate_threshold"]):
        recommendations.insert(0, "This segment exceeds the configured churn-rate alert threshold; review the segment and verify the sample before action.")
    return {
        "filters": {"telecom_partner": request.telecom_partner, "state": request.state, "focus": request.focus},
        "summary": summary,
        "partner_breakdown": partner,
        "state_breakdown": state,
        "usage_summary": usage,
        "findings": [f"{summary['churned_customers']:,} of {summary['total_customers']:,} selected customers are labelled churned.", f"Observed churn rate in this segment is {summary['churn_rate']:.2f}%."] + warnings,
        "recommendations": recommendations,
        "limitations": ["These are descriptive associations, not causal explanations.", "The current trained model has ROC-AUC near 0.50 and is not suitable for reliable customer-level risk ranking."],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/report.csv")
def download_report():
    df = _data()
    # Export customer records without exposing internal model predictions.
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    filename = f"churniq_customer_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/alerts")
def get_alert_settings():
    with _alert_lock:
        return {**_alert_settings, "note": "Settings are persisted locally in backend/runtime/alert_settings.json. Protect this runtime folder in deployments."}


@router.put("/alerts")
def update_alert_settings(settings: AlertSettings):
    with _alert_lock:
        _alert_settings.update(settings.model_dump())
        _persist_alert_settings()
        return {**_alert_settings, "message": "Alert settings saved to local runtime storage."}


@router.get("/alerts/evaluate")
def evaluate_alerts():
    df = _data()
    with _alert_lock:
        settings = dict(_alert_settings)
    snapshot = _evaluate_snapshot(df, settings)
    snapshot["source"] = "manual"
    _append_history(snapshot)
    return {**snapshot, "note": "Thresholds are also checked periodically by the background monitor. Aggregate report snapshots are written locally; no raw customer rows are included."}


@router.get("/alerts/history")
def alert_history(limit: int = 20):
    limit = min(max(limit, 1), 100)
    if not _HISTORY_PATH.exists():
        return {"items": [], "count": 0}
    items = []
    try:
        for line in _HISTORY_PATH.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not read alert history.") from exc
    return {"items": list(reversed(items)), "count": len(items)}

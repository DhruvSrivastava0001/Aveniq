
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.analytics.data_loader import load_customer_data

router = APIRouter()


def _load_dataset() -> pd.DataFrame:
    """Load customer records from the shared Spring Boot/MySQL loader."""
    try:
        df = load_customer_data()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not load customer data from Spring Boot/MySQL. "
                "Check that the Spring Boot API and database are running."
            ),
        ) from exc

    required = {"telecom_partner", "state", "churn"}
    missing = required.difference(df.columns)

    if missing:
        raise HTTPException(
            status_code=500,
            detail=(
                "Customer data is missing required columns: "
                + ", ".join(sorted(missing))
            ),
        )

    df = df.copy()

    # Normalize partner and state values.
    for column in ("telecom_partner", "state"):
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Keep only records with valid binary churn labels.
    df["churn"] = pd.to_numeric(df["churn"], errors="coerce")
    df = df[df["churn"].isin([0, 1])].copy()
    df["churn"] = df["churn"].astype(int)

    return df


def _stats_by(df: pd.DataFrame, column: str) -> list[dict]:
    """Calculate customer counts and observed churn rates by group."""
    if df.empty:
        return []

    grouped = (
        df.groupby(column, dropna=False)
        .agg(
            customers=("churn", "size"),
            churned=("churn", "sum"),
        )
        .reset_index()
    )

    grouped["churn_rate"] = (
        grouped["churned"] / grouped["customers"] * 100
    )

    grouped = grouped.sort_values(
        "churn_rate",
        ascending=False,
        kind="stable",
    )

    result = []

    for _, row in grouped.iterrows():
        name = row[column]

        result.append(
            {
                column: "Unknown" if pd.isna(name) else str(name),
                "customers": int(row["customers"]),
                "churned": int(row["churned"]),
                "churn_rate": round(float(row["churn_rate"]), 2),
            }
        )

    return result


def _summary(df: pd.DataFrame) -> dict:
    """Summarize valid customer records."""
    total = int(len(df))
    churned = int(df["churn"].sum()) if total else 0

    return {
        "total_customers": total,
        "churned_customers": churned,
        "non_churned_customers": total - churned,
        "churn_rate": (
            round(churned / total * 100, 2) if total else 0.0
        ),
    }


def _insights(stats: list[dict], name_key: str) -> dict:
    """Return highest and lowest observed churn rates."""
    if not stats:
        return {
            f"highest_churn_{name_key}": None,
            "highest_churn_rate": 0.0,
            f"lowest_churn_{name_key}": None,
            "lowest_churn_rate": 0.0,
        }

    highest = max(stats, key=lambda item: item["churn_rate"])
    lowest = min(stats, key=lambda item: item["churn_rate"])

    return {
        f"highest_churn_{name_key}": highest[name_key],
        "highest_churn_rate": highest["churn_rate"],
        f"lowest_churn_{name_key}": lowest[name_key],
        "lowest_churn_rate": lowest["churn_rate"],
    }


@router.get("/api/business-insights/filtered")
def get_filtered_business_insights(
    telecom_partner: str | None = Query(default=None),
    state: str | None = Query(default=None),
):
    """Calculate business metrics after applying optional filters."""
    df = _load_dataset()

    # Preserve dropdown options from the complete dataset.
    available_partners = sorted(
        df["telecom_partner"].dropna().unique().tolist()
    )
    available_states = sorted(
        df["state"].dropna().unique().tolist()
    )

    telecom_partner = (
        telecom_partner.strip() if telecom_partner else None
    )
    state = state.strip() if state else None

    if telecom_partner:
        if telecom_partner not in available_partners:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Unknown telecom_partner. Available values: "
                    + ", ".join(available_partners)
                ),
            )

        df = df[df["telecom_partner"] == telecom_partner]

    if state:
        if state not in available_states:
            raise HTTPException(
                status_code=422,
                detail="Unknown state value.",
            )

        df = df[df["state"] == state]

    partner_stats = _stats_by(df, "telecom_partner")
    state_stats = _stats_by(df, "state")

    return {
        "summary": _summary(df),
        "partner_stats": partner_stats,
        "state_stats": state_stats,
        "partner_insights": _insights(
            partner_stats,
            "telecom_partner",
        ),
        "state_insights": _insights(state_stats, "state"),
        "available_states": available_states,
        "filters": {
            "telecom_partners": available_partners,
            "states": available_states,
            "selected_partner": telecom_partner or "",
            "selected_state": state or "",
        },
        "data_source": "mysql",
    }

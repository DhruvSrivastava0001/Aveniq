
from pathlib import Path

import pandas as pd
from fastapi import HTTPException


# Project root:
# Customer-Churn-Analysis/
# ├── data/cleaned/telecom_churn_cleaned.csv
# └── backend/app/analytics/business_insights.py

BASE_DIR = Path(__file__).resolve().parents[3]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "cleaned"
    / "telecom_churn_cleaned.csv"
)


def normalize_partner_name(value) -> str:
    """Standardize known telecom partner aliases."""

    if pd.isna(value):
        return "Unknown"

    name = " ".join(str(value).strip().split())
    normalized = name.lower().replace(".", "").replace(" ", "")
    normalized = normalized.replace("_", "").replace("-", "")

    if normalized in {"jio", "reliancejio"}:
        return "Reliance Jio"

    if normalized in {
        "vi",
        "vodafone",
        "vodafoneidea",
        "vodafoneindia",
    }:
        return "Vi"

    if normalized == "airtel":
        return "Airtel"

    if normalized == "bsnl":
        return "BSNL"

    return name


def load_dataset() -> pd.DataFrame:
    """Load, validate, and normalize the cleaned customer dataset."""

    if not DATA_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                f"Cleaned dataset not found at: {DATA_PATH}. "
                "Check that the CSV exists in the project-root "
                "data/cleaned directory."
            ),
        )

    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read the cleaned dataset.",
        ) from exc

    required_columns = {
        "telecom_partner",
        "state",
        "churn",
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset is missing required columns: "
                + ", ".join(sorted(missing_columns))
            ),
        )

    df["telecom_partner"] = (
        df["telecom_partner"]
        .astype("string")
        .str.strip()
    )

    df["state"] = (
        df["state"]
        .astype("string")
        .str.strip()
    )

    df["churn"] = pd.to_numeric(
        df["churn"],
        errors="coerce",
    )

    # Keep only valid binary churn labels.
    df = df[df["churn"].isin([0, 1])].copy()
    df["churn"] = df["churn"].astype(int)

    # Normalize aliases before filtering and aggregation.
    df["telecom_partner"] = (
        df["telecom_partner"]
        .map(normalize_partner_name)
        .astype("string")
    )

    # Represent missing partner/state values consistently.
    df["telecom_partner"] = (
        df["telecom_partner"].fillna("Unknown")
    )

    df["state"] = (
        df["state"]
        .fillna("Unknown")
        .replace("", "Unknown")
    )

    return df


def calculate_stats(
    df: pd.DataFrame,
    column: str,
) -> list[dict]:
    """Calculate counts and churn rates from grouped customer records."""

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

    # Calculate the rate from combined counts, not averaged rates.
    grouped["churn_rate"] = (
        grouped["churned"]
        / grouped["customers"]
        * 100
    ).round(2)

    grouped = grouped.sort_values(
        ["churn_rate", column],
        ascending=[False, True],
    )

    records = []

    for _, row in grouped.iterrows():
        value = row[column]

        records.append(
            {
                column: (
                    "Unknown" if pd.isna(value) else str(value)
                ),
                "customers": int(row["customers"]),
                "churned": int(row["churned"]),
                "churn_rate": float(row["churn_rate"]),
            }
        )

    return records


def make_insights(
    stats: list[dict],
    name_key: str,
) -> dict:
    """Find the highest and lowest observed churn-rate groups."""

    if not stats:
        return {
            f"highest_churn_{name_key}": None,
            "highest_churn_rate": 0.0,
            f"lowest_churn_{name_key}": None,
            "lowest_churn_rate": 0.0,
        }

    highest = max(
        stats,
        key=lambda item: item["churn_rate"],
    )

    lowest = min(
        stats,
        key=lambda item: item["churn_rate"],
    )

    return {
        f"highest_churn_{name_key}": highest[name_key],
        "highest_churn_rate": highest["churn_rate"],
        f"lowest_churn_{name_key}": lowest[name_key],
        "lowest_churn_rate": lowest["churn_rate"],
    }


def get_business_insights(
    telecom_partner: str | None = None,
    state: str | None = None,
) -> dict:
    """Return business insights for the selected filters."""

    # load_dataset() already normalizes partner aliases.
    df = load_dataset()

    partners = sorted(
        df["telecom_partner"].dropna().unique().tolist()
    )

    states = sorted(
        df["state"].dropna().unique().tolist()
    )

    # Normalize partner filter input as well.
    if telecom_partner:
        telecom_partner = normalize_partner_name(telecom_partner)

        if telecom_partner not in partners:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown telecom partner: {telecom_partner}",
            )

    if state:
        state = " ".join(state.strip().split())

        if state not in states:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown state: {state}",
            )

    # Apply filters to customer-level records.
    if telecom_partner:
        df = df[df["telecom_partner"] == telecom_partner]

    if state:
        df = df[df["state"] == state]

    # Overall summary.
    total_customers = int(len(df))
    churned_customers = (
        int(df["churn"].sum()) if total_customers else 0
    )
    retained_customers = total_customers - churned_customers

    churn_rate = (
        round(churned_customers / total_customers * 100, 2)
        if total_customers
        else 0.0
    )

    # Group statistics for the filtered records.
    partner_stats = calculate_stats(
        df,
        "telecom_partner",
    )

    state_stats = calculate_stats(
        df,
        "state",
    )

    return {
        "summary": {
            "total_customers": total_customers,
            "churned_customers": churned_customers,
            "non_churned_customers": retained_customers,
            "churn_rate": churn_rate,
        },
        "partner_stats": partner_stats,
        "state_stats": state_stats,
        "partner_insights": make_insights(
            partner_stats,
            "telecom_partner",
        ),
        "state_insights": make_insights(
            state_stats,
            "state",
        ),
        "available_states": states,
        "filters": {
            "telecom_partners": partners,
            "states": states,
            "selected_partner": telecom_partner or "",
            "selected_state": state or "",
        },
        "interpretation": (
            "These results describe observed churn patterns. "
            "They do not establish the causes of customer churn."
        ),
    }

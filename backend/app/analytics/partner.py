
import pandas as pd

from app.analytics.data_loader import load_customer_data


def normalize_partner(value):
    """Standardize telecom partner aliases."""
    if pd.isna(value):
        return "Unknown"

    name = str(value).strip()

    if not name:
        return "Unknown"

    aliases = {
        "jio": "Reliance Jio",
        "reliance jio": "Reliance Jio",
        "vodafone": "Vi",
        "vi": "Vi",
    }

    return aliases.get(name.casefold(), name)


def get_partner_churn():
    df = load_customer_data()

    if df.empty:
        return []

    required_columns = {"telecom_partner", "churn"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    df = df.copy()

    df["telecom_partner"] = df["telecom_partner"].map(
        normalize_partner
    )
    df["churn"] = pd.to_numeric(df["churn"], errors="coerce")

    df = df.dropna(subset=["churn"])

    # Only include valid binary churn labels.
    df = df[df["churn"].isin([0, 1])]

    if df.empty:
        return []

    partner_summary = (
        df.groupby("telecom_partner", dropna=False)
        .agg(
            total_customers=("churn", "size"),
            churned_customers=("churn", "sum"),
        )
        .reset_index()
    )

    partner_summary["churn_rate"] = (
        partner_summary["churned_customers"]
        / partner_summary["total_customers"]
        * 100
    ).round(2)

    partner_summary["total_customers"] = (
        partner_summary["total_customers"].astype(int)
    )
    partner_summary["churned_customers"] = (
        partner_summary["churned_customers"].astype(int)
    )

    # Maintain compatibility with the existing React dashboard.
    partner_summary["customers"] = partner_summary["total_customers"]
    partner_summary["churned"] = partner_summary["churned_customers"]

    return (
        partner_summary.sort_values("telecom_partner")
        .reset_index(drop=True)
        .to_dict(orient="records")
    )

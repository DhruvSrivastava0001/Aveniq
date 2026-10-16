import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_tenure_churn():
    df = pd.read_csv(DATA_PATH)

    df["date_of_registration"] = pd.to_datetime(
        df["date_of_registration"],
        errors="coerce"
    )

    analysis_date = df["date_of_registration"].max()

    df["tenure_days"] = (
        analysis_date - df["date_of_registration"]
    ).dt.days

    df["tenure_months"] = (
        df["tenure_days"] / 30.44
    ).round(1)

    df["tenure_group"] = pd.cut(
        df["tenure_months"],
        bins=[-1, 6, 12, 24, 36, 60, float("inf")],
        labels=[
            "0-6 months",
            "7-12 months",
            "13-24 months",
            "25-36 months",
            "37-60 months",
            "60+ months"
        ]
    )

    tenure_summary = (
    df.groupby("tenure_group", observed=True)
    .agg(
        customers=("customer_id", "count"),
        churned=("churn", "sum")
    )
    .reset_index()
)
    tenure_summary["churn_rate"] = (
        tenure_summary["churned"]
        / tenure_summary["customers"]
        * 100
    ).round(2)

    return tenure_summary.to_dict(orient="records")
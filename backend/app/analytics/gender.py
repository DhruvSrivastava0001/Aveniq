import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_gender_churn():
    df = pd.read_csv(DATA_PATH)

    gender_summary = (
        df.groupby("gender")
        .agg(
            customers=("customer_id", "count"),
            churned=("churn", "sum")
        )
        .reset_index()
    )

    gender_summary["churn_rate"] = (
        gender_summary["churned"]
        / gender_summary["customers"]
        * 100
    ).round(2)

    return gender_summary.to_dict(orient="records")
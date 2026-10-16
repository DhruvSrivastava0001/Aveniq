import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_city_churn():
    df = pd.read_csv(DATA_PATH)

    city_summary = (
        df.groupby("city")
        .agg(
            customers=("customer_id", "count"),
            churned=("churn", "sum")
        )
        .reset_index()
    )

    city_summary["churn_rate"] = (
        city_summary["churned"]
        / city_summary["customers"]
        * 100
    ).round(2)

    city_summary = city_summary.sort_values(
        "churn_rate",
        ascending=False
    )

    return city_summary.to_dict(orient="records")
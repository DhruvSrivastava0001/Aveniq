import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_state_churn():
    df = pd.read_csv(DATA_PATH)

    state_summary = (
        df.groupby("state")
        .agg(
            customers=("customer_id", "count"),
            churned=("churn", "sum")
        )
        .reset_index()
    )

    state_summary["churn_rate"] = (
        state_summary["churned"]
        / state_summary["customers"]
        * 100
    ).round(2)

    state_summary = state_summary.sort_values(
        "churn_rate",
        ascending=False
    )

    return state_summary.to_dict(orient="records")
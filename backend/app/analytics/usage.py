import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_usage_summary():
    df = pd.read_csv(DATA_PATH)

    usage_summary = (
        df.groupby("churn")
        .agg(
            customers=("customer_id", "count"),
            avg_calls=("calls_made", "mean"),
            avg_sms=("sms_sent", "mean"),
            avg_data=("data_used", "mean")
        )
        .reset_index()
    )

    usage_summary["churn_status"] = usage_summary["churn"].map({
        0: "Non-Churned",
        1: "Churned"
    })

    usage_summary = usage_summary.drop(columns=["churn"])

    usage_columns = [
        "avg_calls",
        "avg_sms",
        "avg_data"
    ]

    usage_summary[usage_columns] = (
        usage_summary[usage_columns].round(2)
    )

    return usage_summary.to_dict(orient="records")
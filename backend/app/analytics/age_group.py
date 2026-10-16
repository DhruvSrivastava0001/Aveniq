import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_age_group_churn():
    df = pd.read_csv(DATA_PATH)

    df["age_group"] = pd.cut(
        df["age"],
        bins=[0, 17, 25, 35, 45, 55, 65, 100],
        labels=[
            "Under 18",
            "18-25",
            "26-35",
            "36-45",
            "46-55",
            "56-65",
            "65+"
        ]
    )

    age_summary = (
        df.groupby("age_group", observed=False)
        .agg(
            customers=("customer_id", "count"),
            churned=("churn", "sum")
        )
        .reset_index()
    )

    # Remove age groups with no customers.
    # This prevents division by zero and NaN values in the API response.
    age_summary = age_summary[age_summary["customers"] > 0].copy()

    age_summary["churn_rate"] = (
        age_summary["churned"]
        / age_summary["customers"]
        * 100
    ).round(2)

    return age_summary.to_dict(orient="records")
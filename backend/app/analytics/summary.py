
import pandas as pd

from app.analytics.data_loader import load_customer_data


def get_summary():
    """
    Generate customer summary statistics using the shared
    cached data loader connected to MySQL through Spring Boot.
    """
    df = load_customer_data()

    if df.empty or "churn" not in df.columns:
        return {
            "total_customers": 0,
            "churned_customers": 0,
            "non_churned_customers": 0,
            "churn_rate": 0.0,
            "data_source": "mysql",
        }

    churn = pd.to_numeric(df["churn"], errors="coerce")
    valid_churn = churn.isin([0, 1])

    total_customers = int(valid_churn.sum())
    churned_customers = int((churn[valid_churn] == 1).sum())
    non_churned_customers = (
        total_customers - churned_customers
    )

    churn_rate = (
        (churned_customers / total_customers) * 100
        if total_customers > 0
        else 0.0
    )

    return {
        "total_customers": total_customers,
        "churned_customers": churned_customers,
        "non_churned_customers": non_churned_customers,
        "churn_rate": round(churn_rate, 2),
        "data_source": "mysql",
    }

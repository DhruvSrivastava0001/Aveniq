import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def get_customers(
    page: int = 1,
    page_size: int = 10,
    search: str = "",
    churn: int | None = None,
):
    df = pd.read_csv(DATA_PATH)

    # Filter by churn status: 1 = churned, 0 = retained
    if churn is not None:
        df = df[df["churn"] == churn]

    # Search by customer ID, city, or telecom partner
    if search.strip():
        term = search.strip().lower()
        mask = (
            df["customer_id"].astype(str).str.lower().str.contains(term, na=False)
            | df["city"].astype(str).str.lower().str.contains(term, na=False)
            | df["telecom_partner"].astype(str).str.lower().str.contains(term, na=False)
        )
        df = df[mask]

    total = len(df)
    start = (page - 1) * page_size
    result = df.iloc[start:start + page_size].copy()

    # Replace missing values so the response is valid JSON
    result = result.astype(object).where(pd.notna(result), None)

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "customers": result.to_dict(orient="records"),
    }


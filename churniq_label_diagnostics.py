
"""
ChurnIQ label-pattern diagnostics.
Read-only: this script does not modify the dataset or saved models.

Run from the project root:
    .\venv\Scripts\python.exe churniq_label_diagnostics.py
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"


def show_rate(title, frame, group_col, min_count=100):
    print(f"\n--- {title} ---")

    temp = frame[[group_col, "churn"]].copy()
    temp[group_col] = (
        temp[group_col].astype("object").fillna("MISSING").astype(str)
    )

    result = (
        temp.groupby(group_col, dropna=False)["churn"]
        .agg(customers="size", churned="sum", churn_rate="mean")
        .reset_index()
    )

    result = result[result["customers"] >= min_count].copy()
    result["churn_rate_percent"] = (result["churn_rate"] * 100).round(2)

    print(
        result.drop(columns="churn_rate")
        .sort_values("churn_rate_percent", ascending=False)
        .to_string(index=False)
    )


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required = {
        "customer_id", "date_of_registration", "churn", "age",
        "estimated_salary", "num_dependents", "calls_made",
        "sms_sent", "data_used", "telecom_partner", "gender",
        "state", "city",
    }

    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["date_of_registration"] = pd.to_datetime(
        df["date_of_registration"], errors="coerce"
    )
    df["churn"] = pd.to_numeric(df["churn"], errors="coerce")
    df = df.dropna(subset=["churn"]).copy()

    if not df["churn"].isin([0, 1]).all():
        raise ValueError("The churn column must contain only 0, 1, or missing values.")

    df["churn"] = df["churn"].astype(int)

    print("=" * 78)
    print("CHURNIQ LABEL-PATTERN DIAGNOSTICS — READ ONLY")
    print("=" * 78)
    print(f"Rows checked: {len(df):,}")
    print(f"Overall churn rate: {df['churn'].mean() * 100:.3f}%")
    print(f"Unique churn labels: {sorted(df['churn'].unique().tolist())}")
    print(f"Customer IDs unique: {df['customer_id'].is_unique}")
    print(
        "Registration dates missing/unparseable: "
        f"{df['date_of_registration'].isna().sum():,}"
    )

    # Churn by customer-ID decile.
    ordered = df.sort_values("customer_id").copy()
    ordered["customer_id_band"] = pd.qcut(
        ordered["customer_id"].rank(method="first"),
        q=10,
        labels=[f"Decile {i}" for i in range(1, 11)],
    )
    show_rate("CHURN RATE BY CUSTOMER-ID DECILE", ordered, "customer_id_band", 1)

    # Churn by registration month.
    date_df = df.dropna(subset=["date_of_registration"]).copy()
    date_df["registration_month"] = (
        date_df["date_of_registration"].dt.to_period("M").astype(str)
    )
    show_rate(
        "CHURN RATE BY REGISTRATION MONTH",
        date_df,
        "registration_month",
        100,
    )

    # Churn by quantile bins for numeric predictors.
    numeric_columns = [
        "age", "estimated_salary", "num_dependents",
        "calls_made", "sms_sent", "data_used",
    ]

    print("\n--- CHURN RATE BY NUMERIC FEATURE BINS ---")

    for col in numeric_columns:
        work = df[[col, "churn"]].copy()
        work[col] = pd.to_numeric(work[col], errors="coerce")
        valid = work.dropna(subset=[col]).copy()

        if valid[col].nunique() < 2:
            print(f"\n{col}: not enough distinct values to bin")
            continue

        try:
            bin_col = f"{col}_bin"
            valid[bin_col] = pd.qcut(
                valid[col], q=5, duplicates="drop"
            ).astype(str)

            show_rate(f"{col}", valid, bin_col, 100)

        except ValueError as exc:
            print(f"\n{col}: could not create bins ({exc})")

    # Check whether missing usage values relate to churn.
    print("\n--- CHURN RATE BY USAGE-VALUE MISSINGNESS ---")

    for col in ["calls_made", "sms_sent", "data_used"]:
        temp = df[["churn", col]].copy()
        temp["value_status"] = temp[col].isna().map(
            {True: "Missing", False: "Present"}
        )

        result = temp.groupby("value_status")["churn"].agg(
            customers="size",
            churned="sum",
            churn_rate="mean",
        )
        result["churn_rate_percent"] = (
            result["churn_rate"] * 100
        ).round(3)

        print(f"\n{col}:")
        print(result.drop(columns="churn_rate").to_string())

    # Churn rates across categorical features.
    for col in ["telecom_partner", "gender", "state", "city"]:
        show_rate(f"CHURN RATE BY {col.upper()}", df, col, 100)

    print("\n" + "=" * 78)
    print("READING THE RESULTS")
    print("=" * 78)
    print("- Compare churn rates across groups; small differences may be noise.")
    print("- Look for large, repeatable differences, not just tiny rate changes.")
    print("- Customer-ID patterns may indicate ordering effects, not causal behaviour.")
    print("- These descriptive checks do not prove labels are random or synthetic.")
    print("- No dataset or model files were changed.")


if __name__ == "__main__":
    main()

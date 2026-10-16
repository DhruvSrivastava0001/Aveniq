
from pathlib import Path
import pandas as pd

# Locate the dataset
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"

# Load data without modifying the CSV
df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("CHURN LABEL INSPECTION")
print("=" * 60)

# 1. Check available columns
print("\n1. Available columns:")
print(df.columns.tolist())

# 2. Check whether the two columns exist
print("\n2. Required columns:")

for col in ["churn", "predicted_churn"]:
    print(f"{col}: {'Found' if col in df.columns else 'Not found'}")

# Stop if the original target is missing
if "churn" not in df.columns:
    raise ValueError("The dataset does not contain the 'churn' column.")

# 3. Inspect the original churn labels
print("\n3. Original churn distribution:")
print(df["churn"].value_counts(dropna=False).sort_index())

print("\nOriginal churn percentages:")
print(
    (df["churn"].value_counts(normalize=True, dropna=False) * 100)
    .round(2)
)

# 4. Compare predictions if the column exists
if "predicted_churn" in df.columns:
    comparison = df[["churn", "predicted_churn"]].dropna().copy()

    print("\n4. Predicted churn distribution:")
    print(comparison["predicted_churn"].value_counts().sort_index())

    print("\n5. Agreement between churn and predicted_churn:")

    agreement = (
        comparison["churn"] == comparison["predicted_churn"]
    ).mean() * 100

    print(f"Rows compared: {len(comparison):,}")
    print(f"Agreement: {agreement:.2f}%")

    print("\n6. Cross-tabulation:")
    print(
        pd.crosstab(
            comparison["churn"],
            comparison["predicted_churn"],
            rownames=["Actual churn"],
            colnames=["Predicted churn"],
        )
    )
else:
    print(
        "\nThe cleaned CSV does not contain predicted_churn. "
        "No comparison was performed."
    )

print("\nInspection complete. No files were modified.")


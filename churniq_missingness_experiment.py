"""
ChurnIQ Experiment B: Test whether missing usage values carry churn signal.

READ-ONLY:
- Reads data/cleaned/telecom_churn_cleaned.csv
- Does not save or overwrite datasets, models, notebooks, or app files.
- Compares the current feature set with the same features plus three missingness indicators.

Run from the project root:
    python churniq_missingness_experiment.py
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "cleaned" / "telecom_churn_cleaned.csv"
TARGET = "churn"

CATEGORICAL_FEATURES = ["telecom_partner", "gender", "state", "city"]
NUMERIC_FEATURES = [
    "age",
    "num_dependents",
    "estimated_salary",
    "calls_made",
    "sms_sent",
    "data_used",
    "tenure_months",
    "registration_year",
]
USAGE_FEATURES = ["calls_made", "sms_sent", "data_used"]
MISSING_FEATURES = [f"{column}_missing" for column in USAGE_FEATURES]


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at:\n{DATA_PATH}\n"
            "Save this script in the ChurnIQ project root and check the dataset path."
        )

    df = pd.read_csv(DATA_PATH)

    required = {
        TARGET, "customer_id", "date_of_registration",
        *CATEGORICAL_FEATURES, *NUMERIC_FEATURES[:6], *USAGE_FEATURES,
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df["date_of_registration"] = pd.to_datetime(
        df["date_of_registration"], errors="coerce"
    )
    if df["date_of_registration"].isna().any():
        raise ValueError("Some registration dates could not be parsed.")

    analysis_date = df["date_of_registration"].max()
    tenure_days = (analysis_date - df["date_of_registration"]).dt.days
    df["tenure_months"] = (tenure_days / 30.44).round(1)
    df["registration_year"] = df["date_of_registration"].dt.year

    # Preserve missingness before the numeric imputers fill the original values.
    for column, indicator in zip(USAGE_FEATURES, MISSING_FEATURES):
        df[indicator] = df[column].isna().astype("int8")

    return df


def build_pipeline(categorical_features, numeric_features):
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])
    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )),
    ])


def evaluate(name, model, x_test, y_test):
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, list(model.classes_).index(1)]
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])

    print(f"\n{name}")
    print("-" * len(name))
    print(f"ROC-AUC:  {roc_auc_score(y_test, probabilities):.4f}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print(f"Precision (churn=1): {precision_score(y_test, predictions, zero_division=0):.4f}")
    print(f"Recall (churn=1):    {recall_score(y_test, predictions, zero_division=0):.4f}")
    print(f"F1-score (churn=1):  {f1_score(y_test, predictions, zero_division=0):.4f}")
    print("Confusion matrix [[TN, FP], [FN, TP]]:")
    print(matrix)
    return roc_auc_score(y_test, probabilities)


def main():
    print("=" * 72)
    print("CHURNIQ MISSINGNESS EXPERIMENT — READ ONLY")
    print("=" * 72)
    print(f"Dataset: {DATA_PATH}")

    df = load_data()
    print(f"Rows: {len(df):,}")
    print(f"Overall churn rate: {df[TARGET].mean() * 100:.3f}%")
    print("\nMissing-value counts used to build indicators:")
    for column in USAGE_FEATURES:
        print(f"  {column}: {int(df[column].isna().sum()):,}")

    base_features = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    expanded_features = base_features + MISSING_FEATURES

    # One shared split makes the comparison fair.
    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.20,
        random_state=42,
        stratify=df[TARGET],
    )
    y_train = df.loc[train_idx, TARGET].astype(int)
    y_test = df.loc[test_idx, TARGET].astype(int)

    baseline = build_pipeline(CATEGORICAL_FEATURES, NUMERIC_FEATURES)
    expanded_numeric = NUMERIC_FEATURES + MISSING_FEATURES
    with_indicators = build_pipeline(CATEGORICAL_FEATURES, expanded_numeric)

    print("\nTraining baseline (existing 12 features)...")
    baseline.fit(df.loc[train_idx, base_features], y_train)
    baseline_auc = evaluate(
        "EXPERIMENT A — BASELINE FEATURES",
        baseline, df.loc[test_idx, base_features], y_test,
    )

    print("\nTraining model with three missingness indicators...")
    with_indicators.fit(df.loc[train_idx, expanded_features], y_train)
    expanded_auc = evaluate(
        "EXPERIMENT B — BASELINE + MISSINGNESS INDICATORS",
        with_indicators, df.loc[test_idx, expanded_features], y_test,
    )

    difference = expanded_auc - baseline_auc
    print("\n" + "=" * 72)
    print("COMPARISON")
    print("=" * 72)
    print(f"Baseline ROC-AUC:             {baseline_auc:.4f}")
    print(f"With indicators ROC-AUC:      {expanded_auc:.4f}")
    print(f"ROC-AUC change (B - A):       {difference:+.4f}")
    if difference >= 0.01:
        print("Interpretation: improvement is noticeable on this split; validate before adopting.")
    elif difference > 0:
        print("Interpretation: small improvement on this split; it may be noise.")
    elif difference <= -0.01:
        print("Interpretation: performance decreased noticeably on this split.")
    else:
        print("Interpretation: little to no ROC-AUC change on this split.")

    print("\nIMPORTANT:")
    print("- This experiment does not save or overwrite any files.")
    print("- A single split is preliminary; use cross-validation before drawing firm conclusions.")
    print("- Near-0.50 ROC-AUC means weak ranking ability, even if accuracy looks higher.")
    print("- Do not replace the production model based on this experiment alone.")


if __name__ == "__main__":
    main()

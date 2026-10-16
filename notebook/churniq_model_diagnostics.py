"""
ChurnIQ Model Diagnostics
-------------------------
Run this script before changing or retraining the existing churn model.

What it does:
- Finds telecom_churn_cleaned.csv in common project locations.
- Checks target values, class balance, missing values, duplicate rows,
  numeric summaries, categorical churn rates, and numeric correlations.
- Evaluates a baseline DummyClassifier and LogisticRegression using a
  stratified train/test split and preprocessing fitted only on training data.

This script does not overwrite your existing model or modify your dataset.
Install dependencies if needed:
    pip install pandas numpy scikit-learn
Run from your project root:
    python churniq_model_diagnostics.py
"""

from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "churn"
RANDOM_STATE = 42

CANDIDATE_PATHS = [
    Path("data/cleaned/telecom_churn_cleaned.csv"),
    Path("../data/cleaned/telecom_churn_cleaned.csv"),
    Path("telecom_churn_cleaned.csv"),
    Path("data/telecom_churn_cleaned.csv"),
]


def find_dataset():
    for path in CANDIDATE_PATHS:
        if path.exists():
            return path
    print("Could not find telecom_churn_cleaned.csv.")
    print("Place this script in your project root, or update CANDIDATE_PATHS.")
    sys.exit(1)


def print_section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main():
    csv_path = find_dataset()
    df = pd.read_csv(csv_path)

    print_section("1. DATASET OVERVIEW")
    print(f"File: {csv_path.resolve()}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")
    print("Columns:", list(df.columns))

    if TARGET not in df.columns:
        print(f"\nERROR: Expected target column '{TARGET}' was not found.")
        print("Update TARGET in this script to match your dataset.")
        sys.exit(1)

    print_section("2. TARGET DISTRIBUTION")
    print("Counts (including missing):")
    print(df[TARGET].value_counts(dropna=False))
    print("\nPercentages:")
    print((df[TARGET].value_counts(normalize=True, dropna=False) * 100).round(2))
    print("\nUnique target values:", df[TARGET].dropna().unique())

    print_section("3. MISSING VALUES")
    missing = df.isna().sum().sort_values(ascending=False)
    print(missing[missing > 0] if missing.any() else "No missing values found.")

    print_section("4. DUPLICATE ROWS")
    print(f"Exact duplicate rows: {df.duplicated().sum():,}")

    print_section("5. NUMERIC FEATURE SUMMARY")
    numeric = df.select_dtypes(include=np.number)
    print(numeric.describe().T.round(3).to_string())

    print_section("6. CATEGORICAL CHURN RATES")
    categorical_candidates = [
        "telecom_partner", "gender", "state", "city"
    ]
    found_categorical = [c for c in categorical_candidates if c in df.columns]
    if not found_categorical:
        print("No expected categorical columns found.")
    for col in found_categorical:
        print(f"\n{col}:")
        summary = (
            df.groupby(col, dropna=False)[TARGET]
            .agg(customers="size", churn_rate="mean")
        )
        summary["churn_rate_percent"] = (summary["churn_rate"] * 100).round(2)
        print(summary.drop(columns="churn_rate").sort_values(
            "churn_rate_percent", ascending=False
        ).head(15).to_string())

    print_section("7. NUMERIC CORRELATIONS WITH TARGET")
    numeric = df.select_dtypes(include=np.number)
    if TARGET in numeric.columns:
        corr = numeric.corr(numeric_only=True)[TARGET].drop(TARGET)
        print(corr.reindex(corr.abs().sort_values(ascending=False).index).round(4))
    else:
        print("Target is not numeric. Check target encoding before correlation analysis.")

    print_section("8. MODEL EVALUATION")
    model_df = df.dropna(subset=[TARGET]).copy()
    y = model_df[TARGET]

    # Ensure a binary target with values 0/1. Convert only if labels are clearly binary.
    unique_values = list(pd.Series(y.unique()).dropna())
    if set(unique_values) == {0, 1} or set(unique_values) == {0.0, 1.0}:
        y = y.astype(int)
    else:
        print("Target values are not exactly {0, 1}.")
        print("Map the target to 0/1 intentionally before relying on these metrics.")
        print("Skipping model evaluation to avoid silently changing labels.")
        return

    X = model_df.drop(columns=[TARGET])

    # Exclude obvious identifier columns from this diagnostic baseline.
    id_like = [
        c for c in X.columns
        if c.lower() in {"id", "customer_id", "customerid", "row_id", "index"}
    ]
    if id_like:
        print("Excluded identifier-like columns:", id_like)
        X = X.drop(columns=id_like)

    if y.nunique() != 2:
        print("Target does not contain two classes; skipping model evaluation.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    numeric_features = X_train.select_dtypes(include=np.number).columns.tolist()
    categorical_features = [
        c for c in X_train.columns if c not in numeric_features
    ]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocess = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])

    models = {
        "Dummy baseline (most frequent)": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(
            max_iter=2000, random_state=RANDOM_STATE
        ),
        "Balanced Logistic Regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        ),
    }

    print(f"Training rows: {len(X_train):,}; test rows: {len(X_test):,}")
    print("Training churn rate:", round(float(y_train.mean() * 100), 2), "%")
    print("Test churn rate:", round(float(y_test.mean() * 100), 2), "%")
    print("Numeric features:", numeric_features)
    print("Categorical features:", categorical_features)

    for name, estimator in models.items():
        print(f"\n--- {name} ---")
        pipe = Pipeline([("preprocess", preprocess), ("model", estimator)])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe.fit(X_train, y_train)

        predictions = pipe.predict(X_test)
        print(f"Accuracy:          {accuracy_score(y_test, predictions):.4f}")
        print(f"Balanced accuracy: {balanced_accuracy_score(y_test, predictions):.4f}")
        print(f"Precision:         {precision_score(y_test, predictions, zero_division=0):.4f}")
        print(f"Recall:            {recall_score(y_test, predictions, zero_division=0):.4f}")
        print(f"F1:                {f1_score(y_test, predictions, zero_division=0):.4f}")
        print("Confusion matrix [[TN, FP], [FN, TP]]:")
        print(confusion_matrix(y_test, predictions, labels=[0, 1]))
        print("Classification report:")
        print(classification_report(y_test, predictions, zero_division=0))

        if hasattr(pipe, "predict_proba"):
            probabilities = pipe.predict_proba(X_test)[:, 1]
            if len(np.unique(y_test)) == 2:
                print(f"ROC-AUC:           {roc_auc_score(y_test, probabilities):.4f}")

    print_section("9. INTERPRETATION NOTES")
    print(
        "- Compare Logistic Regression with the Dummy baseline, not accuracy alone.\n"
        "- ROC-AUC near 0.50 indicates weak ranking ability on this test split.\n"
        "- Correlation and group churn rates are descriptive, not causal.\n"
        "- This script uses a single stratified holdout; consider cross-validation\n"
        "  before drawing firm conclusions.\n"
        "- No model files or dataset files were changed."
    )


if __name__ == "__main__":
    main()

"""
ChurnIQ Experiment C: 5-fold stratified cross-validation
--------------------------------------------------------
Read-only experiment: this script does NOT save or modify the dataset,
trained model, or any project files. It prints fold-level metrics and
summary statistics to the terminal.

Run from the ChurnIQ project root:
    python churniq_cross_validation_experiment.py

Required packages:
    pandas, numpy, scikit-learn
"""

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_PATH = Path("data/cleaned/telecom_churn_cleaned.csv")
RANDOM_STATE = 42
N_SPLITS = 5


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH.resolve()}\n"
            "Run this script from the ChurnIQ project root folder."
        )

    df = pd.read_csv(DATA_PATH)
    required = {
        "date_of_registration", "churn", "telecom_partner", "gender",
        "age", "state", "city", "num_dependents", "estimated_salary",
        "calls_made", "sms_sent", "data_used",
    }
    missing_columns = sorted(required - set(df.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    df["date_of_registration"] = pd.to_datetime(
        df["date_of_registration"], errors="coerce"
    )
    if df["date_of_registration"].isna().any():
        raise ValueError("Some registration dates could not be parsed.")

    # Match the feature engineering used in the current training notebook.
    analysis_date = df["date_of_registration"].max()
    tenure_days = (analysis_date - df["date_of_registration"]).dt.days
    df["tenure_months"] = (tenure_days / 30.44).round(1)
    df["registration_year"] = df["date_of_registration"].dt.year

    feature_columns = [
        "telecom_partner",
        "gender",
        "age",
        "state",
        "city",
        "num_dependents",
        "estimated_salary",
        "calls_made",
        "sms_sent",
        "data_used",
        "tenure_months",
        "registration_year",
    ]
    X = df[feature_columns].copy()
    y = df["churn"].astype(int)

    numeric_features = [
        "age", "num_dependents", "estimated_salary", "calls_made",
        "sms_sent", "data_used", "tenure_months", "registration_year",
    ]
    categorical_features = ["telecom_partner", "gender", "state", "city"]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=RANDOM_STATE,
            )),
        ]
    )

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    metric_rows = []
    print("=" * 68)
    print("ChurnIQ — Experiment C: 5-Fold Stratified Cross-Validation")
    print("=" * 68)
    print(f"Rows: {len(df):,}")
    print(f"Features: {len(feature_columns)}")
    print(f"Churn rate: {y.mean():.2%}")
    print("Model: balanced Logistic Regression")
    print("No model or dataset files will be saved or changed.\n")

    for fold_number, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]

        row = {
            "fold": fold_number,
            "roc_auc": roc_auc_score(y_test, probabilities),
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1": f1_score(y_test, predictions, zero_division=0),
        }
        metric_rows.append(row)
        print(
            f"Fold {fold_number}: "
            f"ROC-AUC={row['roc_auc']:.4f} | "
            f"Accuracy={row['accuracy']:.4f} | "
            f"Precision={row['precision']:.4f} | "
            f"Recall={row['recall']:.4f} | "
            f"F1={row['f1']:.4f}"
        )

    results = pd.DataFrame(metric_rows)
    print("\n" + "-" * 68)
    print("SUMMARY (mean ± standard deviation across folds)")
    print("-" * 68)
    for metric in ["roc_auc", "accuracy", "precision", "recall", "f1"]:
        print(
            f"{metric.upper():<10} "
            f"{results[metric].mean():.4f} ± {results[metric].std(ddof=1):.4f}"
        )

    auc_mean = results["roc_auc"].mean()
    print("\nInterpretation:")
    if auc_mean < 0.52:
        print(
            "Mean ROC-AUC is very close to 0.50. The current features/model "
            "show little ability to rank churners above non-churners on these "
            "random stratified folds."
        )
    else:
        print(
            "Mean ROC-AUC is above 0.52. Inspect fold-to-fold variation and "
            "compare against a time-based holdout before making performance claims."
        )
    print(
        "\nCaution: random cross-validation does not test future-period "
        "generalization. This script also follows the notebook's existing "
        "dataset-wide tenure reference date; a later time-based evaluation "
        "should calculate tenure using the training cutoff/reference date."
    )


if __name__ == "__main__":
    main()

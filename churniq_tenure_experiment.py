
"""
ChurnIQ Experiment E: Test the effect of tenure_months.

READ-ONLY:
- Reads the cleaned dataset.
- Does not modify datasets or notebooks.
- Does not save or overwrite the production model.

Run from the project root:
    python churniq_tenure_experiment.py
"""

from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "cleaned" / "telecom_churn_cleaned.csv"
TARGET = "churn"
RANDOM_STATE = 42


def build_model(numeric_features, categorical_features):
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
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
            random_state=RANDOM_STATE,
        )),
    ])


def evaluate_model(name, model, X_test, y_test):
    probabilities = model.predict_proba(X_test)[
        :, list(model.classes_).index(1)
    ]
    predictions = model.predict(X_test)

    results = {
        "Model": name,
        "ROC-AUC": roc_auc_score(y_test, probabilities),
        "Average precision": average_precision_score(
            y_test, probabilities
        ),
        "Accuracy": accuracy_score(y_test, predictions),
        "Precision": precision_score(
            y_test, predictions, zero_division=0
        ),
        "Recall": recall_score(
            y_test, predictions, zero_division=0
        ),
        "F1": f1_score(y_test, predictions, zero_division=0),
    }

    for metric, value in results.items():
        if metric != "Model":
            print(f"{metric:20s}: {value:.4f}")

    return results


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required = {
        TARGET,
        "date_of_registration",
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
    }

    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df.dropna(subset=[TARGET]).copy()

    if not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError("The churn target must contain only 0 and 1.")

    df[TARGET] = df[TARGET].astype(int)

    # Reproduce the original notebook's tenure calculation for comparison.
    df["date_of_registration"] = pd.to_datetime(
        df["date_of_registration"], errors="coerce"
    )

    if df["date_of_registration"].isna().any():
        raise ValueError("Some registration dates could not be parsed.")

    analysis_date = df["date_of_registration"].max()

    df["tenure_months"] = (
        (analysis_date - df["date_of_registration"]).dt.days / 30.44
    ).round(1)

    df["registration_year"] = df["date_of_registration"].dt.year

    categorical_features = [
        "telecom_partner",
        "gender",
        "state",
        "city",
    ]

    numeric_with_tenure = [
        "age",
        "num_dependents",
        "estimated_salary",
        "calls_made",
        "sms_sent",
        "data_used",
        "tenure_months",
        "registration_year",
    ]

    numeric_without_tenure = [
        feature for feature in numeric_with_tenure
        if feature != "tenure_months"
    ]

    features_with_tenure = (
        categorical_features + numeric_with_tenure
    )
    features_without_tenure = (
        categorical_features + numeric_without_tenure
    )

    # Use one shared split for a fair comparison.
    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=df[TARGET],
    )

    y_train = df.loc[train_idx, TARGET]
    y_test = df.loc[test_idx, TARGET]

    print("=" * 72)
    print("CHURNIQ TENURE EXPERIMENT — READ ONLY")
    print("=" * 72)
    print(f"Rows: {len(df):,}")
    print(f"Training rows: {len(train_idx):,}")
    print(f"Testing rows: {len(test_idx):,}")
    print(f"Test churn rate: {y_test.mean():.2%}")
    print("\nModel A: Original features, including tenure_months")

    model_a = build_model(
        numeric_with_tenure, categorical_features
    )
    model_a.fit(
        df.loc[train_idx, features_with_tenure], y_train
    )
    results_a = evaluate_model(
        "With tenure",
        model_a,
        df.loc[test_idx, features_with_tenure],
        y_test,
    )

    print("\nModel B: Same features, excluding tenure_months")

    model_b = build_model(
        numeric_without_tenure, categorical_features
    )
    model_b.fit(
        df.loc[train_idx, features_without_tenure], y_train
    )
    results_b = evaluate_model(
        "Without tenure",
        model_b,
        df.loc[test_idx, features_without_tenure],
        y_test,
    )

    print("\n" + "=" * 72)
    print("COMPARISON")
    print("=" * 72)

    comparison = pd.DataFrame([results_a, results_b])
    print(comparison.to_string(
        index=False,
        formatters={
            metric: "{:.4f}".format
            for metric in [
                "ROC-AUC",
                "Average precision",
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
            ]
        },
    ))

    print(
        "\nROC-AUC change without tenure: "
        f"{results_b['ROC-AUC'] - results_a['ROC-AUC']:+.4f}"
    )

    print("\nInterpretation limits:")
    print("- This is one stratified random holdout, not final validation.")
    print("- The experiment tests predictive usefulness, not causality.")
    print("- Registration-derived tenure may not represent actual tenure")
    print("  at the time the churn label was observed.")
    print("- No files were saved or overwritten.")


if __name__ == "__main__":
    main()

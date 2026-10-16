"""
ChurnIQ model comparison experiment.

This script:
- Reproduces the feature engineering and 80/20 stratified split
  used in 03_Model_Training.ipynb.
- Compares a dummy baseline, logistic regression, balanced logistic
  regression, and a Random Forest.
- Does NOT save or overwrite any model or dataset.
Run from the ChurnIQ project root:
    python churniq_model_experiment.py
"""

from pathlib import Path
import time
import warnings

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
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

warnings.filterwarnings("ignore", category=UserWarning)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"
RANDOM_STATE = 42


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at:\n{DATA_PATH}\n"
            "Run this script from your ChurnIQ project folder and check the data path."
        )

    print("=" * 78)
    print("CHURNIQ MODEL COMPARISON — EXPERIMENT ONLY")
    print("=" * 78)
    print(f"Dataset: {DATA_PATH}")
    print("No model or dataset files will be changed.\n")

    df = pd.read_csv(DATA_PATH)

    # Match the date feature engineering in 03_Model_Training.ipynb.
    df["date_of_registration"] = pd.to_datetime(
        df["date_of_registration"], errors="coerce"
    )
    analysis_date = df["date_of_registration"].max()
    df["tenure_days"] = (
        analysis_date - df["date_of_registration"]
    ).dt.days
    df["tenure_months"] = (df["tenure_days"] / 30.44).round(1)
    df["registration_year"] = df["date_of_registration"].dt.year

    features = [
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
    target = "churn"

    # Fail clearly if the dataset has unexpected labels or missing required columns.
    missing_columns = [column for column in features + [target] if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Required columns missing from dataset: {missing_columns}")

    df = df.dropna(subset=[target]).copy()
    X = df[features]
    y = df[target].astype(int)

    numeric_features = [
        "age",
        "num_dependents",
        "estimated_salary",
        "calls_made",
        "sms_sent",
        "data_used",
        "tenure_months",
        "registration_year",
    ]
    categorical_features = ["telecom_partner", "gender", "state", "city"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"Rows: {len(df):,}")
    print(f"Training rows: {len(X_train):,} | Test rows: {len(X_test):,}")
    print(f"Training churn rate: {y_train.mean() * 100:.2f}%")
    print(f"Test churn rate: {y_test.mean() * 100:.2f}%")
    print(f"Features: {len(features)}")
    print("\nPreparing preprocessing pipelines...")

    def make_preprocessor():
        numeric_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        categorical_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        return ColumnTransformer(
            [
                ("numeric", numeric_pipeline, numeric_features),
                ("categorical", categorical_pipeline, categorical_features),
            ]
        )

    models = [
        (
            "Dummy baseline",
            DummyClassifier(strategy="most_frequent"),
        ),
        (
            "Logistic Regression",
            LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        ),
        (
            "Balanced Logistic Regression",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
        ),
        (
            "Random Forest (balanced)",
            RandomForestClassifier(
                n_estimators=120,
                max_depth=14,
                min_samples_leaf=25,
                class_weight="balanced_subsample",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
    ]

    results = []

    for name, estimator in models:
        print("\n" + "-" * 78)
        print(f"Training: {name}")
        start = time.time()

        pipeline = Pipeline(
            [
                ("preprocessor", make_preprocessor()),
                ("model", estimator),
            ]
        )
        pipeline.fit(X_train, y_train)

        predictions = pipeline.predict(X_test)
        probabilities = pipeline.predict_proba(X_test)[:, 1]

        metrics = {
            "Model": name,
            "Accuracy": accuracy_score(y_test, predictions),
            "Balanced accuracy": balanced_accuracy_score(y_test, predictions),
            "Precision": precision_score(y_test, predictions, zero_division=0),
            "Recall": recall_score(y_test, predictions, zero_division=0),
            "F1": f1_score(y_test, predictions, zero_division=0),
            "ROC-AUC": roc_auc_score(y_test, probabilities),
        }
        results.append(metrics)

        print(f"Completed in {time.time() - start:.1f} seconds")
        for metric, value in metrics.items():
            if metric != "Model":
                print(f"{metric:20s}: {value:.4f}")
        print("Confusion matrix [[TN, FP], [FN, TP]]:")
        print(confusion_matrix(y_test, predictions))
        print("Classification report:")
        print(classification_report(y_test, predictions, zero_division=0))

    print("\n" + "=" * 78)
    print("SUMMARY — compare ROC-AUC and churn recall, not accuracy alone")
    print("=" * 78)
    summary = pd.DataFrame(results).sort_values("ROC-AUC", ascending=False)
    print(summary.to_string(index=False, formatters={
        "Accuracy": "{:.4f}".format,
        "Balanced accuracy": "{:.4f}".format,
        "Precision": "{:.4f}".format,
        "Recall": "{:.4f}".format,
        "F1": "{:.4f}".format,
        "ROC-AUC": "{:.4f}".format,
    }))

    print("\nInterpretation:")
    print("- ROC-AUC near 0.50 means weak ranking ability on this test split.")
    print("- Higher recall usually means finding more churners, but may increase false alarms.")
    print("- This is a single holdout experiment, not proof of general performance.")
    print("- No model or dataset files were saved or overwritten.")


if __name__ == "__main__":
    main()


"""
ChurnIQ Experiment D — Time-based evaluation + label/date inspection
--------------------------------------------------------------------
Read-only diagnostic script. It does NOT save or modify project files,
the dataset, or the trained model.

Run from the ChurnIQ project root:
    python churniq_time_based_diagnostics.py

This script:
1. Inspects available date columns and churn-label values.
2. Reports churn rates by registration month.
3. Runs a chronological holdout using registration date as a proxy.
4. Fits preprocessing steps on training data only.
5. Does not save a model.

Important: registration-date splitting is not necessarily a true
future-churn evaluation. See the printed interpretation limits.
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_PATH = Path("data/cleaned/telecom_churn_cleaned.csv")
TARGET = "churn"
DATE_COLUMN = "date_of_registration"
TEST_FRACTION = 0.20
RANDOM_STATE = 42


def print_section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH.resolve()}\n"
            "Run this script from the ChurnIQ project root."
        )

    df = pd.read_csv(DATA_PATH)

    print_section("1. DATASET AND LABEL INSPECTION")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print("Columns:", ", ".join(map(str, df.columns)))

    if TARGET not in df.columns or DATE_COLUMN not in df.columns:
        raise ValueError(
            f"Required columns are missing: {TARGET}, {DATE_COLUMN}"
        )

    print(f"\nTarget column: {TARGET}")
    print("Target values including missing:")
    print(df[TARGET].value_counts(dropna=False).sort_index().to_string())
    print("\nTarget dtype:", df[TARGET].dtype)

    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")

    if (
        df[TARGET].isna().any()
        or not set(df[TARGET].unique()).issubset({0, 1})
    ):
        raise ValueError(
            "This script expects a complete binary churn target encoded as 0/1."
        )

    print("Overall churn rate:", f"{df[TARGET].mean():.2%}")

    date_columns = [
        col for col in df.columns
        if "date" in str(col).lower() or "time" in str(col).lower()
    ]

    print(
        "\nColumns whose names contain 'date' or 'time':",
        date_columns or "None",
    )

    for col in date_columns:
        parsed = pd.to_datetime(df[col], errors="coerce")
        valid = parsed.notna()

        print(
            f"  {col}: parseable={valid.sum():,}/{len(df):,}; "
            f"range={parsed[valid].min() if valid.any() else 'N/A'} "
            f"to {parsed[valid].max() if valid.any() else 'N/A'}"
        )

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")

    if df[DATE_COLUMN].isna().any():
        raise ValueError("Some registration dates could not be parsed.")

    print_section("2. CHURN RATE BY REGISTRATION MONTH")

    monthly = (
        df.assign(
            registration_month=df[DATE_COLUMN].dt.to_period("M").astype(str)
        )
        .groupby("registration_month", observed=True)[TARGET]
        .agg(rows="size", churn_rate="mean")
    )

    monthly["churn_rate_pct"] = monthly["churn_rate"] * 100

    print(
        monthly[["rows", "churn_rate_pct"]].to_string(
            formatters={
                "churn_rate_pct": lambda value: f"{value:.2f}%"
            }
        )
    )

    print_section("3. TIME-BASED HOLDOUT")

    df = df.sort_values(
        DATE_COLUMN, kind="mergesort"
    ).reset_index(drop=True)

    split_index = int(len(df) * (1 - TEST_FRACTION))

    if split_index <= 0 or split_index >= len(df):
        raise ValueError(
            "The dataset is too small for the configured test fraction."
        )

    # Use the first row of the intended test portion as the cutoff.
    # All records from the cutoff date remain together in the test set.
    cutoff = df.iloc[split_index][DATE_COLUMN]

    train_df = df[df[DATE_COLUMN] < cutoff].copy()
    test_df = df[df[DATE_COLUMN] >= cutoff].copy()

    if train_df.empty or test_df.empty:
        raise ValueError(
            "The chronological split produced an empty training or test set."
        )

    last_train_date = train_df[DATE_COLUMN].max()
    first_test_date = test_df[DATE_COLUMN].min()

    print(
        "Split rule: earliest records for training and latest records "
        "for testing, keeping each registration date in one set."
    )
    print(f"Target split index: {split_index:,}")
    print(f"Cutoff date: {cutoff}")
    print(f"Training rows: {len(train_df):,}")
    print(f"Testing rows:  {len(test_df):,}")
    print(f"Last training registration date: {last_train_date}")
    print(f"First testing registration date: {first_test_date}")
    print(f"Training churn rate: {train_df[TARGET].mean():.2%}")
    print(f"Testing churn rate:  {test_df[TARGET].mean():.2%}")

    if last_train_date >= first_test_date:
        raise ValueError(
            "Chronological split validation failed: the last training "
            "date must be earlier than the first testing date."
        )

    # Registration year is derived from each row's own registration date.
    # We do not create tenure_months because no valid observation date
    # is available to calculate customer tenure without extra assumptions.
    for part in (train_df, test_df):
        part["registration_year"] = part[DATE_COLUMN].dt.year

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
        "registration_year",
    ]

    missing_train = [
        col for col in feature_columns + [TARGET]
        if col not in train_df.columns
    ]
    missing_test = [
        col for col in feature_columns + [TARGET]
        if col not in test_df.columns
    ]

    if missing_train or missing_test:
        raise ValueError(
            f"Missing training columns: {missing_train}; "
            f"missing testing columns: {missing_test}"
        )

    X_train = train_df[feature_columns]
    y_train = train_df[TARGET].astype(int)
    X_test = test_df[feature_columns]
    y_test = test_df[TARGET].astype(int)

    numeric_features = [
        "age",
        "num_dependents",
        "estimated_salary",
        "calls_made",
        "sms_sent",
        "data_used",
        "registration_year",
    ]

    categorical_features = [
        "telecom_partner",
        "gender",
        "state",
        "city",
    ]

    preprocess = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "onehot",
                        OneHotEncoder(handle_unknown="ignore"),
                    ),
                ]),
                categorical_features,
            ),
        ]
    )

    model = Pipeline([
        ("preprocessing", preprocess),
        (
            "classifier",
            LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=RANDOM_STATE,
            ),
        ),
    ])

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    print("\nHoldout metrics:")
    print(f"ROC-AUC:           {roc_auc_score(y_test, probabilities):.4f}")
    print(
        f"Average precision: "
        f"{average_precision_score(y_test, probabilities):.4f}"
    )
    print(f"Accuracy:          {accuracy_score(y_test, predictions):.4f}")
    print(
        f"Precision:         "
        f"{precision_score(y_test, predictions, zero_division=0):.4f}"
    )
    print(
        f"Recall:            "
        f"{recall_score(y_test, predictions, zero_division=0):.4f}"
    )
    print(
        f"F1-score:          "
        f"{f1_score(y_test, predictions, zero_division=0):.4f}"
    )

    print_section("4. INTERPRETATION LIMITS")
    print(
        "- This evaluates later registration cohorts, not necessarily "
        "future churn events.\n"
        "- A valid future-churn forecast needs a defined prediction date, "
        "an observation window, and a later churn-label window.\n"
        "- Registration year is included as a feature; no tenure feature "
        "is created because a valid observation date is unavailable.\n"
        "- The script cannot verify how the existing churn labels were "
        "generated.\n"
        "- Nothing was saved. The dataset and trained model remain untouched."
    )


if __name__ == "__main__":
    main()

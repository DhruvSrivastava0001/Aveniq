
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = Path("data/candidate/telco_customer_churn.csv")

df = pd.read_csv(DATA_PATH)

# Validate the target.
df = df.dropna(subset=["Churn"]).copy()
df["Churn"] = df["Churn"].astype(str).str.strip()

if not set(df["Churn"].unique()).issubset({"Yes", "No"}):
    raise ValueError("Unexpected values found in the Churn column.")

y = df["Churn"].map({"No": 0, "Yes": 1})

# CustomerID is an identifier, not a useful predictor.
X = df.drop(columns=["Churn", "customerID"], errors="ignore").copy()

# TotalCharges may be read as text; convert it to numeric.
if "TotalCharges" in X.columns:
    X["TotalCharges"] = pd.to_numeric(
        X["TotalCharges"], errors="coerce"
    )

numeric_cols = X.select_dtypes(include="number").columns.tolist()
categorical_cols = X.select_dtypes(exclude="number").columns.tolist()

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_cols),
    ("categorical", categorical_pipeline, categorical_cols),
])

models = {
    "Dummy baseline": DummyClassifier(strategy="prior"),
    "Logistic Regression": LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

scoring = {
    "accuracy": "accuracy",
    "balanced_accuracy": "balanced_accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "roc_auc": "roc_auc",
}

print("Dataset rows:", len(df))
print("Features:", X.shape[1])
print("Churn rate:", round(y.mean() * 100, 2), "%")
print("Numeric features:", numeric_cols)
print("Categorical features:", categorical_cols)

for name, model in models.items():
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])

    scores = cross_validate(
        pipeline,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
        error_score="raise",
    )

    print(f"\n--- {name} (5-fold CV) ---")
    for metric in scoring:
        values = scores[f"test_{metric}"]
        print(
            f"{metric}: {values.mean():.4f} "
            f"+/- {values.std():.4f}"
        )

print("\nExperiment complete. No production model was saved or replaced.")

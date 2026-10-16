
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
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

DATA_PATH = Path("data/candidate/telco_customer_churn.csv")
MODEL_PATH = Path("data/candidate/churn_model_ibm_candidate.joblib")

THRESHOLD = 0.55

df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["Churn"]).copy()
df["Churn"] = df["Churn"].astype(str).str.strip()

if not set(df["Churn"].unique()).issubset({"Yes", "No"}):
    raise ValueError("Unexpected values in Churn column.")

y = df["Churn"].map({"No": 0, "Yes": 1})
X = df.drop(columns=["Churn", "customerID"], errors="ignore")

X["TotalCharges"] = pd.to_numeric(
    X["TotalCharges"], errors="coerce"
)

numeric_cols = X.select_dtypes(include="number").columns.tolist()
categorical_cols = X.select_dtypes(exclude="number").columns.tolist()

preprocessor = ColumnTransformer([
    ("numeric", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]), numeric_cols),
    ("categorical", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical_cols),
])

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
    )),
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

pipeline.fit(X_train, y_train)

probabilities = pipeline.predict_proba(X_test)[:, 1]
predictions = (probabilities >= THRESHOLD).astype(int)

print("Held-out test results")
print("Training rows:", len(X_train))
print("Test rows:", len(X_test))
print("Threshold:", THRESHOLD)
print(f"ROC-AUC: {roc_auc_score(y_test, probabilities):.4f}")
print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
print(f"Balanced accuracy: {balanced_accuracy_score(y_test, predictions):.4f}")
print(f"Precision: {precision_score(y_test, predictions, zero_division=0):.4f}")
print(f"Recall: {recall_score(y_test, predictions, zero_division=0):.4f}")
print(f"F1-score: {f1_score(y_test, predictions, zero_division=0):.4f}")
print("\nConfusion matrix [ [TN, FP], [FN, TP] ]:")
print(confusion_matrix(y_test, predictions, labels=[0, 1]))
print("\nClassification report:")
print(classification_report(
    y_test, predictions,
    target_names=["No churn", "Churn"],
    zero_division=0,
))

# Save separately; never overwrite the production model.
joblib.dump({
    "pipeline": pipeline,
    "threshold": THRESHOLD,
    "feature_columns": X.columns.tolist(),
    "dataset": str(DATA_PATH),
}, MODEL_PATH)

print(f"\nCandidate model saved to: {MODEL_PATH}")
print("Existing production model was not changed.")

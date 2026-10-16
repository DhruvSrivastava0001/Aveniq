
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned" / "telecom_churn_cleaned.csv"

df = pd.read_csv(DATA_PATH)
df = df[df["churn"].isin([0, 1])].copy()

# Exclude identifiers and fields that can act as identifiers.
# Keep registration date as year/month features.
df["date_of_registration"] = pd.to_datetime(
    df["date_of_registration"], errors="coerce"
)
df["registration_year"] = df["date_of_registration"].dt.year
df["registration_month"] = df["date_of_registration"].dt.month

numeric_features = [
    "age", "num_dependents", "estimated_salary",
    "calls_made", "sms_sent", "data_used",
    "registration_year", "registration_month",
]
categorical_features = [
    "telecom_partner", "gender", "state", "city"
]

X = df[numeric_features + categorical_features]
y = df["churn"].astype(int)

preprocessor = ColumnTransformer([
    ("numeric", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]), numeric_features),
    ("categorical", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=1000)),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("Running 5-fold cross-validation...")
probabilities = cross_val_predict(
    model, X, y, cv=cv, method="predict_proba", n_jobs=-1
)[:, 1]

print(f"Rows evaluated: {len(df):,}")
print(f"Baseline ROC-AUC: 0.500")
print(f"Model ROC-AUC: {roc_auc_score(y, probabilities):.4f}")
print("No dataset or production model files were changed.")


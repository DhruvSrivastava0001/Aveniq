
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

df = pd.read_csv("data/candidate/telco_customer_churn.csv")
df = df.dropna(subset=["Churn"]).copy()

y = df["Churn"].astype(str).str.strip().map({"No": 0, "Yes": 1})
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

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
    )),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Each customer's probability is produced by a model
# that did not train on that customer's fold.
probabilities = cross_val_predict(
    model, X, y,
    cv=cv,
    method="predict_proba",
    n_jobs=1,
)[:, 1]

print(f"Out-of-fold ROC-AUC: {roc_auc_score(y, probabilities):.4f}")
print("\nThreshold | Precision | Recall | F1 | TP | FP | FN | TN")
print("-" * 65)

for threshold in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(
        y, predictions, labels=[0, 1]
    ).ravel()

    print(
        f"{threshold:9.2f} | "
        f"{precision_score(y, predictions, zero_division=0):9.3f} | "
        f"{recall_score(y, predictions, zero_division=0):6.3f} | "
        f"{f1_score(y, predictions, zero_division=0):.3f} | "
        f"{tp:4d} | {fp:4d} | {fn:4d} | {tn:4d}"
    )

print("\nNo production model or application files were changed.")

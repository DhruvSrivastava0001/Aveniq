
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "candidate"
    / "churn_model_ibm_candidate.joblib"
)


@lru_cache(maxsize=1)
def load_ibm_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"IBM candidate model not found: {MODEL_PATH}"
        )

    saved = joblib.load(MODEL_PATH)

    return (
        saved["pipeline"],
        float(saved["threshold"]),
        saved["feature_columns"],
    )


def predict_ibm_churn(customer_data: dict):
    try:
        pipeline, threshold, feature_columns = load_ibm_model()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not load the IBM candidate model.",
        ) from exc

    try:
        # Keep exactly the feature names and order used in training.
        customer_df = pd.DataFrame(
            [customer_data],
            columns=feature_columns,
        )

        probability = float(
            pipeline.predict_proba(customer_df)[0][1]
        )

        prediction = int(probability >= threshold)

        return {
            "model": "IBM Telco Churn Candidate",
            "predicted_churn": prediction,
            "prediction_label": (
                "Churn" if prediction == 1 else "No Churn"
            ),
            "churn_probability": round(probability, 4),
            "threshold": threshold,
            "notice": (
                "Experimental prediction based on the IBM Telco "
                "dataset; not a guarantee of customer behavior."
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Could not generate a prediction from these features.",
        ) from exc

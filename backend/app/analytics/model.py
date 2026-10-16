
import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "models" / "churn_model.joblib"

# Load the trained machine learning model
model = joblib.load(MODEL_PATH)


def predict_churn(customer_data):
    # Convert customer details into a DataFrame
    df = pd.DataFrame([customer_data])

    # Predict whether the customer may churn
    prediction = int(model.predict(df)[0])

    # Get the probability associated with churn class 1
    probabilities = model.predict_proba(df)[0]
    churn_index = list(model.classes_).index(1)
    probability = float(probabilities[churn_index])

    # Return the prediction and additional information
    return {
        "prediction": prediction,
        "prediction_label": (
            "Potential Churn"
            if prediction == 1
            else "Potential Retention"
        ),
        "churn_probability": round(probability, 4),
        "model_reliability": "Limited",
        "note": (
            "The model has shown limited ability to distinguish "
            "churners from non-churners. Use this result for "
            "demonstration and further analysis, not as a standalone "
            "customer-retention decision."
        )
    }


# Test the model when this file is run directly
if __name__ == "__main__":
    sample_customer = {
        "telecom_partner": "Airtel",
        "gender": "M",
        "age": 30,
        "state": "Karnataka",
        "city": "Bangalore",
        "num_dependents": 2,
        "estimated_salary": 85000,
        "calls_made": 50,
        "sms_sent": 25,
        "data_used": 5000,
        "tenure_months": 24.0,
        "registration_year": 2022
    }

    print(predict_churn(sample_customer))
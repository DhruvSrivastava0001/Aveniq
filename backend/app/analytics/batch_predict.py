
import io
import logging

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.analytics.ibm_model import load_ibm_model


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_ROWS = 10000

REQUIRED_COLUMNS = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
]


def assess_risk(probability: float) -> dict:
    """Assign a business risk category and practical retention actions."""

    percentage = probability * 100

    if percentage >= 75:
        return {
            "risk_category": "Critical",
            "risk_description": "Immediate retention review recommended.",
            "retention_recommendations": [
                "Prioritize personal outreach to understand the customer's concerns.",
                "Review recent billing issues and service complaints.",
                "Evaluate suitable contract, pricing, or support options.",
            ],
        }

    if percentage >= 55:
        return {
            "risk_category": "High",
            "risk_description": "Proactive retention outreach recommended.",
            "retention_recommendations": [
                "Contact the customer to understand potential dissatisfaction.",
                "Review service quality and billing history.",
                "Discuss suitable plan or support options.",
            ],
        }

    if percentage >= 30:
        return {
            "risk_category": "Medium",
            "risk_description": "Monitor the account for signs of dissatisfaction.",
            "retention_recommendations": [
                "Review contract type and service usage.",
                "Check for unresolved support or billing concerns.",
                "Consider a relevant engagement or loyalty offer.",
            ],
        }

    return {
        "risk_category": "Low",
        "risk_description": "Continue routine customer engagement.",
        "retention_recommendations": [
            "Maintain regular customer communication.",
            "Monitor service experience and satisfaction.",
        ],
    }


async def predict_batch(file: UploadFile) -> dict:
    """Validate an IBM-format CSV and predict churn for each customer."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded CSV file is empty.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File is too large. Maximum supported size is 5 MB.",
            )

        try:
            dataframe = pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Could not read the CSV. Check its format and encoding.",
            ) from exc

    finally:
        await file.close()

    # Normalize surrounding whitespace in column names.
    dataframe.columns = [
        str(column).strip() for column in dataframe.columns
    ]

    if dataframe.empty:
        raise HTTPException(
            status_code=400,
            detail="The CSV contains no customer rows.",
        )

    if len(dataframe) > MAX_ROWS:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum supported batch size is {MAX_ROWS} rows.",
        )

    if dataframe.columns.duplicated().any():
        raise HTTPException(
            status_code=400,
            detail="The CSV contains duplicate column names.",
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The CSV does not match the IBM Telco model schema.",
                "missing_columns": missing_columns,
                "required_columns": REQUIRED_COLUMNS,
            },
        )

    # Load the candidate model and prepare its exact feature schema.
    try:
        pipeline, threshold, feature_columns = load_ibm_model()

        missing_model_columns = [
            column
            for column in feature_columns
            if column not in dataframe.columns
        ]

        if missing_model_columns:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "The CSV is missing model features.",
                    "missing_columns": missing_model_columns,
                },
            )

        model_data = dataframe[feature_columns].copy()

        # Convert numeric columns while allowing blank cells.
        numeric_columns = [
            "SeniorCitizen",
            "tenure",
            "MonthlyCharges",
            "TotalCharges",
        ]

        for column in numeric_columns:
            original = model_data[column]

            # Empty or whitespace-only cells are treated as missing.
            original_clean = original.replace(
                r"^\s*$",
                pd.NA,
                regex=True,
            )

            converted = pd.to_numeric(
                original_clean,
                errors="coerce",
            )

            # Reject invalid non-empty values, such as "unknown".
            invalid = original_clean.notna() & converted.isna()

            if invalid.any():
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Column '{column}' contains invalid numeric "
                        "values. Correct the CSV and upload it again."
                    ),
                )

            model_data[column] = converted

        if model_data["SeniorCitizen"].isna().any():
            raise HTTPException(
                status_code=422,
                detail="SeniorCitizen must contain 0 or 1 for every row.",
            )

        if not model_data["SeniorCitizen"].isin([0, 1]).all():
            raise HTTPException(
                status_code=422,
                detail="SeniorCitizen must contain only 0 or 1.",
            )

        if model_data["tenure"].isna().any():
            raise HTTPException(
                status_code=422,
                detail="Tenure is required for every row.",
            )

        if (
            (model_data["tenure"] < 0)
            | (model_data["tenure"] > 100)
        ).any():
            raise HTTPException(
                status_code=422,
                detail="Tenure must be between 0 and 100 months.",
            )

        for column in ["MonthlyCharges", "TotalCharges"]:
            if (model_data[column].dropna() < 0).any():
                raise HTTPException(
                    status_code=422,
                    detail=f"{column} cannot contain negative values.",
                )

        # The trained pipeline handles missing TotalCharges via imputation.
        probabilities = pipeline.predict_proba(model_data)[:, 1]

    except HTTPException:
        raise

    except FileNotFoundError as exc:
        logging.exception("IBM candidate model file was not found")
        raise HTTPException(
            status_code=503,
            detail="The IBM candidate model is not available.",
        ) from exc

    except Exception as exc:
        logging.exception("Batch prediction failed")
        raise HTTPException(
            status_code=500,
            detail=(
                f"Batch prediction failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    results = []

    # Preserve original CSV columns, including customerID if provided.
    for index, probability in enumerate(probabilities):
        probability = float(probability)
        assessment = assess_risk(probability)

        original_row = dataframe.iloc[index].to_dict()
        clean_row = {}

        # Convert pandas/numpy values into JSON-safe Python values.
        for key, value in original_row.items():
            if pd.isna(value):
                clean_row[key] = None
            elif hasattr(value, "item"):
                clean_row[key] = value.item()
            else:
                clean_row[key] = value

        results.append({
            **clean_row,
            "churn_probability": round(probability, 4),
            "predicted_churn": int(probability >= threshold),
            "prediction_label": (
                "Churn" if probability >= threshold else "No Churn"
            ),
            "risk_category": assessment["risk_category"],
            "risk_description": assessment["risk_description"],
            "retention_recommendations": assessment[
                "retention_recommendations"
            ],
        })

    risk_counts = {
        category: sum(
            row["risk_category"] == category for row in results
        )
        for category in ["Low", "Medium", "High", "Critical"]
    }

    return {
        "model": "IBM Telco Churn Candidate",
        "threshold": threshold,
        "total_customers": len(results),
        "predicted_churn": sum(
            row["predicted_churn"] == 1 for row in results
        ),
        "predicted_no_churn": sum(
            row["predicted_churn"] == 0 for row in results
        ),
        "risk_summary": risk_counts,
        "results": results,
        "notice": (
            "Experimental model. Risk categories are business rules, "
            "and predictions are estimates rather than guarantees."
        ),
    }

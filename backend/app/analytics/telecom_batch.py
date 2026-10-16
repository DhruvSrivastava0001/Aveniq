
import io
import logging

import pandas as pd
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.analytics.model import model


MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB
MAX_ROWS = 300_000
# Fixed reference date from the training dataset snapshot (latest registration).
# Do not derive this from each uploaded batch: that would make identical
# customers receive different tenure values depending on which rows were uploaded.
TRAINING_REFERENCE_DATE = pd.Timestamp("2023-05-04")

# Features expected by the existing telecom model.
FEATURE_COLUMNS = [
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

NUMERIC_COLUMNS = [
    "age",
    "num_dependents",
    "estimated_salary",
    "calls_made",
    "sms_sent",
    "data_used",
    "tenure_months",
    "registration_year",
]

REQUIRED_SOURCE_COLUMNS = [
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
    "date_of_registration",
]


def assess_risk(probability: float) -> str:
    """Assign a business risk category from predicted churn probability."""

    if probability >= 0.75:
        return "Critical"
    if probability >= 0.55:
        return "High"
    if probability >= 0.30:
        return "Medium"
    return "Low"


async def predict_telecom_batch(file: UploadFile):
    """Predict telecom churn and return a downloadable CSV report."""

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
                detail="The uploaded CSV is empty.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Maximum supported file size is 30 MB.",
            )
    finally:
        await file.close()

    try:
        dataframe = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the CSV file. Check its format.",
        ) from exc

    dataframe.columns = [
        str(column).strip() for column in dataframe.columns
    ]

    if dataframe.empty:
        raise HTTPException(
            status_code=400,
            detail="The CSV contains no customer records.",
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

    missing = [
        column
        for column in REQUIRED_SOURCE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The CSV does not match the telecom dataset schema.",
                "missing_columns": missing,
                "required_columns": REQUIRED_SOURCE_COLUMNS,
            },
        )

    # Parse the registration date.
    registration_dates = pd.to_datetime(
        dataframe["date_of_registration"],
        errors="coerce",
    )

    if registration_dates.isna().any():
        raise HTTPException(
            status_code=422,
            detail=(
                "Some date_of_registration values are missing or invalid."
            ),
        )

    # Build the feature set expected by the existing model.
    features = dataframe[
        [
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
        ]
    ].copy()

    features["registration_year"] = registration_dates.dt.year

    # Match the training feature engineering with a FIXED training snapshot
    # reference date. Using the uploaded batch's maximum date would make the
    # same customer receive different tenure values across different batches.
    features["tenure_months"] = (
        (TRAINING_REFERENCE_DATE - registration_dates).dt.days / 30.44
    ).round(1).clip(lower=0)

    # Restore the model's expected feature order.
    features = features[FEATURE_COLUMNS].copy()

    # Convert numeric fields. Blank cells become NaN; invalid text is rejected.
    for column in NUMERIC_COLUMNS:
        original = features[column]
        cleaned = original.replace(r"^\s*$", pd.NA, regex=True)
        converted = pd.to_numeric(cleaned, errors="coerce")

        invalid = cleaned.notna() & converted.isna()

        if invalid.any():
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Column '{column}' contains invalid numeric values."
                ),
            )

        features[column] = converted

    try:
        probabilities = model.predict_proba(features)
        classes = list(model.classes_)

        if 1 not in classes:
            raise ValueError(
                "The trained model has no churn class labelled 1."
            )

        churn_index = classes.index(1)
        churn_probabilities = probabilities[:, churn_index]

    except Exception as exc:
        logging.exception("Telecom batch prediction failed")
        raise HTTPException(
            status_code=500,
            detail=(
                "The trained telecom model could not process these features. "
                "Check its expected columns and preprocessing pipeline."
            ),
        ) from exc

    # Add prediction results while preserving the original customer data.
    report = dataframe.copy()

    report["churn_probability"] = churn_probabilities.round(4)
    report["predicted_churn"] = (
        churn_probabilities >= 0.55
    ).astype(int)

    report["prediction_label"] = report["predicted_churn"].map({
        1: "Potential Churn",
        0: "Potential Retention",
    })

    report["risk_category"] = [
        assess_risk(float(probability))
        for probability in churn_probabilities
    ]

    # Return a downloadable CSV instead of a huge JSON response.
    output = io.StringIO()
    report.to_csv(output, index=False)
    csv_text = output.getvalue()

    def csv_chunks():
        # Stream chunks to the client rather than yielding one giant byte blob.
        chunk_size = 1024 * 1024
        for offset in range(0, len(csv_text), chunk_size):
            yield csv_text[offset:offset + chunk_size].encode("utf-8")

    return StreamingResponse(
        csv_chunks(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="churniq_telecom_predictions.csv"'
            )
        },
    )

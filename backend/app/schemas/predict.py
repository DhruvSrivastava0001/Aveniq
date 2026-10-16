
from pydantic import BaseModel, Field
from typing import Literal


class PredictRequest(BaseModel):

    telecom_partner: Literal[
        "Airtel",
        "Reliance Jio",
        "Vodafone",
        "BSNL"
    ] = Field(..., description="Customer's telecom provider")

    gender: Literal["M", "F"] = Field(
        ..., description="Customer's gender"
    )

    age: int = Field(..., ge=0, le=120)
    state: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)

    num_dependents: int = Field(..., ge=0)
    estimated_salary: float = Field(..., ge=0)

    calls_made: float = Field(..., ge=0)
    sms_sent: float = Field(..., ge=0)
    data_used: float = Field(..., ge=0)

    tenure_months: float = Field(..., ge=0)
    registration_year: int = Field(..., ge=2020, le=2023)
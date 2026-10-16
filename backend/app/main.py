
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.analytics.telecom_batch import predict_telecom_batch
from app.analytics.summary import get_summary
from app.analytics.partner import get_partner_churn
from app.analytics.state import get_state_churn
from app.analytics.gender import get_gender_churn
from app.analytics.city import get_city_churn
from app.analytics.age_group import get_age_group_churn
from app.analytics.tenure import get_tenure_churn
from app.analytics.usage import get_usage_summary
from app.analytics.model import predict_churn
from app.analytics.business_insights import get_business_insights
from app.analytics.customers import get_customers
from app.analytics.data_loader import invalidate_customer_cache
from app.schemas.predict import PredictRequest
from app.business_insights_filtered import (
    router as filtered_insights_router,
)
from app.intelligence import router as intelligence_router, monitoring_loop
from app.analytics.ibm_model import predict_ibm_churn
from app.schemas.ibm_predict import IBMPredictRequest
from fastapi import File, UploadFile
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from app.analytics.batch_predict import predict_batch
@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(monitoring_loop(), name="churniq-monitoring")
    try:
        yield
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    lifespan=lifespan,
    title="Customer Churn Intelligence API",
    description=(
        "Backend API for customer churn analytics "
        "and AI-powered business insights"
    ),
    version="1.0.0",
)


# Register filtered business insights routes.
app.include_router(filtered_insights_router)
app.include_router(intelligence_router)


# Allow requests from the React frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Customer Churn Intelligence API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health():
    """Liveness check that does not require the database to be available."""
    import platform
    import sklearn

    expected_sklearn = "1.7.2"
    return {
        "status": "ok",
        "service": "churniq-python-api",
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "expected_scikit_learn_version": expected_sklearn,
        "model_compatibility": "compatible_version" if sklearn.__version__ == expected_sklearn else "version_mismatch",
        "model_compatibility_note": (
            "Installed scikit-learn matches the serialized model's pinned version."
            if sklearn.__version__ == expected_sklearn else
            f"The model was saved with scikit-learn {expected_sklearn}; install backend/requirements.txt in the active environment."
        ),
    }


@app.get("/api/summary")
def summary():
    return get_summary()


@app.get("/api/churn-by-partner")
def churn_by_partner():
    return get_partner_churn()


@app.get("/api/churn-by-state")
def churn_by_state():
    return get_state_churn()


@app.get("/api/churn-by-gender")
def churn_by_gender():
    return get_gender_churn()


@app.get("/api/churn-by-city")
def churn_by_city():
    return get_city_churn()


@app.get("/api/churn-by-age-group")
def churn_by_age_group():
    return get_age_group_churn()


@app.get("/api/churn-by-tenure")
def churn_by_tenure():
    return get_tenure_churn()


@app.get("/api/usage-summary")
def usage_summary():
    return get_usage_summary()


@app.post("/api/predict")
def predict(customer_data: PredictRequest):
    return predict_churn(customer_data.dict())


@app.get("/api/business-insights")
def business_insights(
    telecom_partner: str | None = None,
    state: str | None = None,
):
    return get_business_insights(
        telecom_partner=telecom_partner,
        state=state,
    )


@app.post("/internal/cache/invalidate")
def invalidate_cache():
    invalidate_customer_cache()
    return {"message": "Customer analytics cache invalidated"}






@app.get("/api/customers")
def customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str = "",
    churn: int | None = Query(default=None, ge=0, le=1),
):
    if churn not in (None, 0, 1):
        raise HTTPException(
            status_code=422,
            detail="Churn must be 0, 1, or omitted.",
        )

    return get_customers(
        page=page,
        page_size=page_size,
        search=search,
        churn=churn,
    )


@app.post("/api/ibm-predict")
def predict_ibm(customer_data: IBMPredictRequest):
    return predict_ibm_churn(customer_data.dict())


@app.post("/api/batch-predict")
async def batch_predict_endpoint(file: UploadFile = File(...)):
    return await predict_batch(file)



@app.post("/api/telecom-batch-predict")
async def telecom_batch_predict_endpoint(
    file: UploadFile = File(...),
):
    return await predict_telecom_batch(file)
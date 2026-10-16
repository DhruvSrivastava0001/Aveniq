# ChurnIQ QA and Runbook

## Important configuration

The React app's Python API default is `http://127.0.0.1:8003`, matching the FastAPI port used during local testing. The API also exposes `GET /health` with runtime versions and a liveness status. Copy `frontend/.env.example` to `frontend/.env.local` if you want explicit local settings. Restart Vite after changing environment variables.

The Python analytics service reads customer data through the Spring Boot service (`SPRING_API_URL`, default `http://localhost:8080`). The customer table UI and CSV import use Spring Boot/MySQL. Configure `DB_USERNAME` and `DB_PASSWORD` in the shell; credentials are no longer hard-coded in `application.properties`. Ensure the database is running and configured in `churniq-backend/backend/src/main/resources/application.properties` before testing CRUD/import features.

## Start services (Windows PowerShell)

Terminal 1 — FastAPI, from project root:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8003 --log-level info
```

Terminal 2 — Spring Boot, from `churniq-backend\backend`:

```powershell
.\mvnw.cmd spring-boot:run
```

Terminal 3 — React, from `frontend`:

```powershell
npm install
npm run dev
```

Open the Vite URL printed in Terminal 3. FastAPI docs: `http://127.0.0.1:8003/docs`.

## Validation checklist

- `GET /` — API health.
- `GET /api/summary`, `/api/churn-by-partner`, `/api/churn-by-state`, `/api/churn-by-gender`, `/api/churn-by-city`, `/api/churn-by-age-group`, `/api/churn-by-tenure`, `/api/usage-summary` — analytics; these depend on the Spring Boot paginated customer endpoint and MySQL.
- `GET /api/customers` — local cleaned CSV-backed list/search endpoint.
- `POST /api/predict` — existing telecom model (limited predictive ability; demonstrative only).
- `POST /api/ibm-predict` — IBM Telco model, separate schema.
- `POST /api/batch-predict` — IBM Telco CSV batch; CSV schema must match IBM dataset.
- `POST /api/telecom-batch-predict` — cleaned telecom CSV batch; expects `date_of_registration` and source columns described by the endpoint validation response.
- `GET /api/business-insights`, `/api/business-insights/filtered` — descriptive insights.
- Intelligence router: `/overview`, `/chat`, `/investigate`, `/report.csv`, `/alerts`, `/alerts/evaluate`, `/alerts/history` (paths are relative to router prefix in `backend/app/intelligence.py`).

## Model compatibility and limitation

`backend/requirements.txt` pins `scikit-learn==1.7.2`, matching the model's training version. If you see `InconsistentVersionWarning` from scikit-learn 1.8.x, install the pinned requirements in the project's active virtual environment:

```powershell
python -m pip install --upgrade "scikit-learn==1.7.2"
python -m pip check
python -c "import sklearn; print(sklearn.__version__)"
```

The final command should print `1.7.2`. The `/health` endpoint now reports the expected version and flags a mismatch. Stop and restart FastAPI after installing. Do not load pickle/joblib model files from untrusted sources.

The telecom batch predictor now derives tenure relative to the fixed training snapshot date (`2023-05-04`), not today's date or each upload's maximum date. This avoids batch-dependent feature drift. Confirm that date matches the actual training dataset before production use.

The existing `models/churn_model.joblib` has previously been identified in code as limited. A successful HTTP 200 only confirms execution, not predictive quality. Do not change the decision threshold simply to force positive churn predictions. Evaluate ROC-AUC, precision, recall, F1, calibration, and a confusion matrix on a held-out dataset before making business claims.

## General-purpose AI assistant

The Intelligence chat can answer general-knowledge, programming, writing, and productivity questions when `OPENAI_API_KEY` is configured for the backend. See `backend/.env.example`. Without a key, the assistant intentionally falls back to deterministic customer-data answers and will explain the supported analytics questions rather than pretending to be a general LLM. Never commit a real API key.

## Button testing

Test every page action against a running backend and database: dashboard refresh/retry; customer create/edit/delete, search, filter, pagination and CSV import/template download; analysis refresh; prediction model switch/submit/reset; insight filter/reset/retry; AI question suggestions, chat submit, investigation, report download, alert save/evaluate/history. Check browser DevTools Console and Network plus the backend terminals for each failure. Some actions require Spring Boot/MySQL or configured environment variables, so they cannot be fully integration-tested from source alone.


## Automated integration smoke test

After MySQL, Spring Boot, and FastAPI are running and the customer table is populated, run from the project root:

```powershell
python scripts/smoke_test.py
```

The non-destructive smoke test checks FastAPI health/version compatibility, Spring Boot's paginated customer endpoint, live intelligence data, one grounded chat question, and alert settings. It does not create/update/delete records and does not replace browser-level button tests. A failure includes the HTTP status or connection error to help identify which service is unavailable.

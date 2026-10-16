"""Focused tests for grounded ChurnIQ intelligence endpoints."""
from fastapi.testclient import TestClient
import pandas as pd
import tempfile
from pathlib import Path

from app.main import app
import app.intelligence as intelligence

client = TestClient(app)

SAMPLE = pd.DataFrame([
    {"customer_id": 1, "telecom_partner": "Airtel", "state": "Karnataka", "city": "Bangalore", "gender": "F", "churn": 1, "calls_made": 10, "sms_sent": 5, "data_used": 500},
    {"customer_id": 2, "telecom_partner": "Airtel", "state": "Karnataka", "city": "Bangalore", "gender": "M", "churn": 0, "calls_made": 20, "sms_sent": 7, "data_used": 700},
    {"customer_id": 3, "telecom_partner": "Jio", "state": "UP", "city": "Kanpur", "gender": "F", "churn": 0, "calls_made": 30, "sms_sent": 9, "data_used": 900},
    {"customer_id": 4, "telecom_partner": "Jio", "state": "UP", "city": "Kanpur", "gender": "M", "churn": 0, "calls_made": 40, "sms_sent": 11, "data_used": 1100},
])


def setup_module():
    intelligence.load_customer_data = lambda: SAMPLE.copy()
    intelligence.os.environ.pop("OPENAI_API_KEY", None)
    test_runtime = Path(tempfile.mkdtemp(prefix="churniq-tests-"))
    intelligence._RUNTIME_DIR = test_runtime
    intelligence._SETTINGS_PATH = test_runtime / "alert_settings.json"
    intelligence._HISTORY_PATH = test_runtime / "alert_history.jsonl"
    intelligence._REPORT_DIR = test_runtime / "reports"
    intelligence._alert_settings.update(intelligence._DEFAULT_ALERT_SETTINGS)


def test_overview_reports_expected_counts():
    response = client.get("/api/intelligence/overview")
    assert response.status_code == 200
    assert response.json()["summary"] == {
        "total_customers": 4,
        "churned_customers": 1,
        "retained_customers": 3,
        "churn_rate": 25.0,
    }


def test_chat_uses_observed_rate_and_discloses_grounding():
    response = client.post("/api/intelligence/chat", json={"question": "What is the overall churn rate?"})
    assert response.status_code == 200
    body = response.json()
    assert "25.00%" in body["answer"]
    assert body["grounded"] is True
    assert body["mode"] == "deterministic"


def test_investigation_applies_partner_filter():
    response = client.post("/api/intelligence/investigate", json={"telecom_partner": "Airtel"})
    assert response.status_code == 200
    assert response.json()["summary"]["total_customers"] == 2
    assert response.json()["summary"]["churn_rate"] == 50.0


def test_alert_threshold_can_be_updated_and_evaluated():
    saved = client.put("/api/intelligence/alerts", json={"churn_rate_threshold": 20, "minimum_segment_size": 1, "enabled": True})
    assert saved.status_code == 200
    evaluated = client.get("/api/intelligence/alerts/evaluate")
    assert evaluated.status_code == 200
    assert any(a["metric"] == "overall_churn_rate" for a in evaluated.json()["alerts"])
    history = client.get("/api/intelligence/alerts/history?limit=5")
    assert history.status_code == 200
    assert history.json()["count"] >= 1


def test_report_is_csv():
    response = client.get("/api/intelligence/report.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "customer_id" in response.text



def test_health_endpoint_reports_runtime_versions():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "churniq-python-api"
    assert body["scikit_learn_version"]


def test_general_question_does_not_require_customer_database(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(intelligence, "_data", lambda: (_ for _ in ()).throw(AssertionError("database should not be loaded")))
    response = client.post("/api/intelligence/chat", json={"question": "Explain Java interfaces in simple words"})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "general_llm_unconfigured"
    assert "OPENAI_API_KEY" in body["answer"]
    assert body["grounded"] is False


def test_general_question_uses_configured_llm_without_customer_rows(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{"message": {"content": "A Java interface defines a contract that classes can implement."}}]}

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(intelligence, "_data", lambda: (_ for _ in ()).throw(AssertionError("database should not be loaded")))
    monkeypatch.setattr(intelligence.requests, "post", lambda *args, **kwargs: FakeResponse())
    response = client.post("/api/intelligence/chat", json={"question": "Explain Java interfaces in simple words"})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "general_llm"
    assert body["grounded"] is False
    assert "defines a contract" in body["answer"]


def test_city_lowest_query_is_respected():
    response = client.post("/api/intelligence/chat", json={"question": "Which city has the lowest churn rate?"})
    assert response.status_code == 200
    assert "lowest observed city-level churn rate" in response.json()["answer"]


def test_general_customer_churn_definition_is_not_misrouted_to_dataset(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(intelligence, "_data", lambda: (_ for _ in ()).throw(AssertionError("database should not be loaded")))
    response = client.post("/api/intelligence/chat", json={"question": "What is customer churn and why does it matter?"})
    assert response.status_code == 200
    assert response.json()["mode"] == "general_llm_unconfigured"

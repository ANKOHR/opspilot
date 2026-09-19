from types import SimpleNamespace

from fastapi.testclient import TestClient
from opspilot_api.main import app


def test_health_contract():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_workflow_listing_is_seeded_and_scoped():
    with TestClient(app) as client:
        response = client.get("/api/workflows", headers={"X-Organization-ID": "demo-org"})
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert {item["id"] for item in response.json()} == {
            "inbound-revenue",
            "ap-exception",
            "support-escalation",
        }


def test_viewer_cannot_start_a_workflow():
    with TestClient(app) as client:
        response = client.post(
            "/api/demo/inbound-lead",
            headers={"X-Organization-ID": "demo-org", "X-Role": "viewer"},
        )
        assert response.status_code == 403


def test_missing_run_returns_not_found_without_cross_tenant_leak():
    with TestClient(app) as client:
        response = client.get(
            "/api/runs/run_does_not_exist",
            headers={"X-Organization-ID": "other-org"},
        )
        assert response.status_code == 404


def test_overview_response_has_operational_metrics():
    with TestClient(app) as client:
        response = client.get("/api/overview", headers={"X-Organization-ID": "demo-org"})
        assert response.status_code == 200
        assert {
            "runs_today",
            "success_rate",
            "waiting_approval",
            "failures",
            "ai_spend_usd",
            "average_runtime_seconds",
            "active_workflows",
        } <= response.json().keys()


def test_loopback_cors_preflight_is_explicit():
    with TestClient(app) as client:
        response = client.options(
            "/api/overview",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_gmail_sync_forwards_targeted_query_to_worker(monkeypatch):
    captured: dict[str, object] = {}

    class FakeSyncJob:
        def send(self, payload):
            captured.update(payload)
            return SimpleNamespace(message_id="job-test-1")

    monkeypatch.setattr("opspilot_api.jobs.sync_gmail_job", FakeSyncJob())

    with TestClient(app) as client:
        response = client.post(
            "/api/integrations/gmail/sync",
            params={"query": 'subject:"OpsPilot verification"', "max_results": 1},
            headers={"X-Organization-ID": "demo-org"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "queued", "job_id": "job-test-1"}
    assert captured["query"] == 'subject:"OpsPilot verification"'
    assert captured["max_results"] == 1

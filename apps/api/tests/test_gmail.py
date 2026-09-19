from __future__ import annotations

import base64
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.fernet import Fernet
from opspilot_api.gmail import (
    GmailConfigurationError,
    authorization_url,
    create_oauth_state,
    decrypt_refresh_token,
    encrypt_refresh_token,
    normalize_message,
    verify_oauth_state,
)
from opspilot_api.schemas import ApprovalStatus, EventIngestRequest
from opspilot_api.tools import DemoToolRegistry


class FakeGmailConnector:
    def __init__(self) -> None:
        self.drafts: list[dict] = []
        self.sent: list[dict] = []

    def search(self, query: str, max_results: int) -> list[dict]:
        return [{"id": "msg_1", "query": query, "max_results": max_results}]

    def read(self, message_id: str) -> dict:
        return {"id": message_id, "body": "hello"}

    def create_draft(self, **arguments: str | None) -> dict:
        draft = {"draft_id": "gmail_draft_1", "status": "created", "external": True, **arguments}
        self.drafts.append(draft)
        return draft

    def send(self, **arguments: str | None) -> dict:
        self.sent.append(arguments)
        return {
            "message_id": "gmail_message_1",
            "status": "sent",
            "provider": "gmail",
            "external": True,
            "sandbox": False,
            "confirmed": True,
        }


def test_oauth_state_is_signed_and_scoped(monkeypatch):
    monkeypatch.setenv("APP_SECRET", "test-app-secret")
    state = create_oauth_state("org-a", "user-a")

    assert verify_oauth_state(state) == {"organisation_id": "org-a", "user_id": "user-a"}
    with pytest.raises(GmailConfigurationError, match="invalid or expired"):
        verify_oauth_state(state + "tampered")


def test_oauth_state_requires_app_secret(monkeypatch):
    monkeypatch.delenv("APP_SECRET", raising=False)
    with pytest.raises(GmailConfigurationError, match="APP_SECRET"):
        create_oauth_state("org-a", "user-a")


def test_authorization_url_preserves_signed_state_and_pkce(monkeypatch):
    monkeypatch.setenv("APP_SECRET", "test-app-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "https://api.example.com/api/integrations/gmail/oauth/callback",
    )

    state = create_oauth_state("org-a", "user-a")
    query = parse_qs(urlparse(authorization_url(state)).query)

    assert query["state"] == [state]
    assert query["code_challenge_method"] == ["S256"]
    assert query["code_challenge"]


def test_exchange_oauth_code_reuses_state_bound_pkce_verifier(monkeypatch):
    monkeypatch.setenv("APP_SECRET", "test-app-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "https://api.example.com/api/integrations/gmail/oauth/callback",
    )
    state = create_oauth_state("org-a", "user-a")
    captured: dict[str, object] = {}

    class FakeFlow:
        credentials = SimpleNamespace(refresh_token="refresh-token", scopes=[])

        def __init__(self):
            self.redirect_uri = None

        def fetch_token(self, **kwargs):
            captured.update(kwargs)

    def fake_from_client_config(_config, **kwargs):
        captured["code_verifier"] = kwargs["code_verifier"]
        captured["autogenerate_code_verifier"] = kwargs["autogenerate_code_verifier"]
        return FakeFlow()

    monkeypatch.setattr("opspilot_api.gmail.Flow.from_client_config", fake_from_client_config)

    from opspilot_api.gmail import exchange_oauth_code

    assert exchange_oauth_code("auth-code", state) is not None
    assert captured["code"] == "auth-code"
    assert captured["code_verifier"]
    assert captured["autogenerate_code_verifier"] is False


def test_gmail_connection_persists_integration_before_credential(runtime):
    _engine, repository = runtime

    connection = repository.upsert_gmail_connection(
        "demo-org",
        "henry.williams85@gmail.com",
        ["https://www.googleapis.com/auth/gmail.readonly"],
        "encrypted-refresh-token",
    )

    assert connection["status"] == "connected"
    stored = repository.gmail_connection("demo-org", include_secret=True)
    assert stored is not None
    assert stored["external_account"] == "henry.williams85@gmail.com"
    assert stored["encrypted_refresh_token"] == "encrypted-refresh-token"


def test_refresh_tokens_are_encrypted(monkeypatch):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    encrypted = encrypt_refresh_token("refresh-token")

    assert encrypted != "refresh-token"
    assert decrypt_refresh_token(encrypted) == "refresh-token"


def test_gmail_message_normalization_decodes_nested_plain_text():
    encoded = base64.urlsafe_b64encode(b"Hello from Gmail").decode().rstrip("=")
    message = normalize_message(
        {
            "id": "msg_1",
            "threadId": "thread_1",
            "snippet": "Hello",
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Subject", "value": "Question"},
                ],
                "parts": [{"mimeType": "text/plain", "body": {"data": encoded}}],
            },
        }
    )

    assert message["from"] == "alice@example.com"
    assert message["subject"] == "Question"
    assert message["body"] == "Hello from Gmail"


def test_live_gmail_tool_is_write_and_approval_gated():
    connector = FakeGmailConnector()
    tools = DemoToolRegistry(gmail_connector=connector)

    draft = tools.execute(
        "gmail.create_draft",
        {"to": "alice@example.com", "subject": "Hello", "body": "Hi"},
        {"gmail.create_draft"},
    )
    assert draft["external"] is True
    with pytest.raises(PermissionError, match="requires human approval"):
        tools.execute("gmail.send", {"draft_id": draft["draft_id"]}, {"gmail.send"})

    sent = tools.execute(
        "gmail.send", {"draft_id": draft["draft_id"]}, {"gmail.send"}, approved=True
    )
    assert sent["status"] == "sent"
    assert connector.sent == [{"draft_id": "gmail_draft_1"}]


def test_live_runtime_records_external_gmail_result(runtime):
    engine, _repository = runtime
    connector = FakeGmailConnector()
    engine.tools = DemoToolRegistry(gmail_connector=connector)
    request = EventIngestRequest(
        idempotency_key="live-gmail-runtime",
        payload={
            "from": "alice@example.com",
            "subject": "Invoice automation",
            "body": "We are a construction company processing 2,000 invoices per month.",
            "thread_id": "thread_1",
        },
    )

    waiting = engine.process_event("demo-org", "tester", request)
    assert waiting["status"] == "waiting_for_approval"
    assert waiting["output"]["gmail_draft"]["external"] is True
    assert waiting["approval_id"]

    completed = engine.decide_approval(
        "demo-org", "tester", waiting["approval_id"], ApprovalStatus.APPROVED, "Approved live test"
    )
    assert completed["output"]["send"]["status"] == "sent"
    assert completed["output"]["send"]["external"] is True
    assert any("via Gmail" in item["message"] for item in completed["trace"])

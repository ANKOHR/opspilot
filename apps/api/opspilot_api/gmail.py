from __future__ import annotations

import base64
import os
from collections.abc import Callable
from email.message import EmailMessage
from typing import Any

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import Resource, build
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
)
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
OAUTH_STATE_SALT = "opspilot-gmail-oauth-v1"


class GmailConfigurationError(RuntimeError):
    """Raised when the live Gmail integration is not configured safely."""


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise GmailConfigurationError(f"{name} is not configured")
    return value


def configured_scopes() -> list[str]:
    configured = os.getenv("GMAIL_SCOPES", "").strip()
    scopes = [item.strip() for item in configured.split(",") if item.strip()]
    return scopes or list(GMAIL_SCOPES)


def _client_config() -> dict[str, Any]:
    return {
        "web": {
            "client_id": _required_env("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": _required_env("GOOGLE_OAUTH_CLIENT_SECRET"),
            "auth_uri": GOOGLE_AUTH_URI,
            "token_uri": GOOGLE_TOKEN_URI,
            "redirect_uris": [_required_env("GOOGLE_OAUTH_REDIRECT_URI")],
        }
    }


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_required_env("APP_SECRET"), salt=OAUTH_STATE_SALT)


def create_oauth_state(organisation_id: str, user_id: str) -> str:
    return _state_serializer().dumps({"organisation_id": organisation_id, "user_id": user_id})


def verify_oauth_state(state: str, max_age: int = 600) -> dict[str, str]:
    try:
        value = _state_serializer().loads(state, max_age=max_age)
    except (BadSignature, SignatureExpired) as exc:
        raise GmailConfigurationError("Gmail OAuth state is invalid or expired") from exc
    if not isinstance(value, dict) or not value.get("organisation_id") or not value.get("user_id"):
        raise GmailConfigurationError("Gmail OAuth state is incomplete")
    return {"organisation_id": str(value["organisation_id"]), "user_id": str(value["user_id"])}


def authorization_url(state: str) -> str:
    flow = Flow.from_client_config(_client_config(), scopes=configured_scopes(), state=state)
    flow.redirect_uri = _required_env("GOOGLE_OAUTH_REDIRECT_URI")
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return url


def exchange_oauth_code(code: str) -> Credentials:
    flow = Flow.from_client_config(_client_config(), scopes=configured_scopes())
    flow.redirect_uri = _required_env("GOOGLE_OAUTH_REDIRECT_URI")
    flow.fetch_token(code=code)
    credentials = flow.credentials
    if not credentials.refresh_token:
        raise GmailConfigurationError(
            "Google did not return a refresh token; reconnect with offline consent"
        )
    return credentials


def encrypt_refresh_token(refresh_token: str) -> str:
    key = _required_env("CREDENTIAL_ENCRYPTION_KEY")
    try:
        return Fernet(key.encode("ascii")).encrypt(refresh_token.encode("utf-8")).decode("ascii")
    except ValueError as exc:
        raise GmailConfigurationError(
            "CREDENTIAL_ENCRYPTION_KEY is not a valid Fernet key"
        ) from exc


def decrypt_refresh_token(encrypted_refresh_token: str) -> str:
    key = _required_env("CREDENTIAL_ENCRYPTION_KEY")
    try:
        return (
            Fernet(key.encode("ascii"))
            .decrypt(encrypted_refresh_token.encode("ascii"))
            .decode("utf-8")
        )
    except ValueError as exc:
        raise GmailConfigurationError(
            "CREDENTIAL_ENCRYPTION_KEY is not a valid Fernet key"
        ) from exc


def _decode_body(value: str) -> str:
    padded = value + ("=" * (-len(value) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")


def _headers(message: dict[str, Any]) -> dict[str, str]:
    return {
        str(item.get("name", "")).lower(): str(item.get("value", ""))
        for item in message.get("payload", {}).get("headers", [])
    }


def _plain_text(part: dict[str, Any]) -> str:
    body = part.get("body") or {}
    if body.get("data") and part.get("mimeType") == "text/plain":
        return _decode_body(str(body["data"]))
    for child in part.get("parts") or []:
        text = _plain_text(child)
        if text:
            return text
    if body.get("data") and not part.get("parts"):
        return _decode_body(str(body["data"]))
    return ""


def normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    headers = _headers(message)
    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "received_at": headers.get("date", ""),
        "snippet": message.get("snippet", ""),
        "body": _plain_text(message.get("payload", {})),
    }


def _raw_message(to: str, subject: str, body: str, thread_id: str | None = None) -> dict[str, Any]:
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")
    payload: dict[str, Any] = {"message": {"raw": encoded}}
    if thread_id:
        payload["message"]["threadId"] = thread_id
    return payload


class GmailConnector:
    """Small Gmail API adapter with normalized outputs and no token exposure."""

    def __init__(
        self,
        service: Resource,
        service_factory: Callable[..., Resource] | None = None,
    ) -> None:
        self.service = service
        self._service_factory = service_factory

    @classmethod
    def from_stored_connection(cls, encrypted_refresh_token: str) -> GmailConnector:
        refresh_token = decrypt_refresh_token(encrypted_refresh_token)
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=_required_env("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=_required_env("GOOGLE_OAUTH_CLIENT_SECRET"),
            scopes=configured_scopes(),
        )
        return cls(build("gmail", "v1", credentials=credentials, cache_discovery=False))

    @classmethod
    def from_credentials(cls, credentials: Credentials) -> GmailConnector:
        return cls(build("gmail", "v1", credentials=credentials, cache_discovery=False))

    def get_profile(self) -> dict[str, Any]:
        return self.service.users().getProfile(userId="me").execute()

    def health_check(self) -> dict[str, Any]:
        profile = self.get_profile()
        return {
            "email": profile.get("emailAddress"),
            "messages_total": profile.get("messagesTotal"),
        }

    def search(self, query: str = "", max_results: int = 20) -> list[dict[str, Any]]:
        response = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max(1, min(max_results, 50)))
            .execute()
        )
        messages: list[dict[str, Any]] = []
        for item in response.get("messages", []):
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=item["id"], format="full")
                .execute()
            )
            messages.append(normalize_message(message))
        return messages

    def read(self, message_id: str) -> dict[str, Any]:
        message = (
            self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        )
        return normalize_message(message)

    def create_draft(
        self, to: str, subject: str, body: str, thread_id: str | None = None
    ) -> dict[str, Any]:
        draft = (
            self.service.users()
            .drafts()
            .create(userId="me", body=_raw_message(to, subject, body, thread_id))
            .execute()
        )
        message = draft.get("message") or {}
        return {
            "draft_id": draft.get("id"),
            "message_id": message.get("id"),
            "thread_id": message.get("threadId") or thread_id,
            "status": "created",
            "provider": "gmail",
            "external": True,
            "sandbox": False,
        }

    def send(self, draft_id: str | None = None, **arguments: Any) -> dict[str, Any]:
        if draft_id:
            response = (
                self.service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
            )
        else:
            response = (
                self.service.users()
                .messages()
                .send(
                    userId="me",
                    body=_raw_message(
                        str(arguments["to"]), str(arguments["subject"]), str(arguments["body"])
                    ),
                )
                .execute()
            )
        return {
            "message_id": response.get("id"),
            "thread_id": response.get("threadId"),
            "status": "sent",
            "provider": "gmail",
            "external": True,
            "sandbox": False,
            "confirmed": True,
        }

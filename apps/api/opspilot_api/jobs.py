from __future__ import annotations

import os
from typing import Any

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from .gmail import GmailConnector

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
dramatiq.set_broker(RedisBroker(url=redis_url))


@dramatiq.actor(max_retries=3, min_backoff=5_000, max_backoff=120_000)
def process_event_job(payload: dict[str, Any]) -> dict[str, Any]:
    """Durable queue boundary; the API remains responsive while workflows run."""
    from .database import init_db
    from .repository import Repository
    from .runtime import WorkflowRuntime
    from .schemas import EventIngestRequest

    init_db()
    repository = Repository()
    repository.seed_demo()
    runtime = WorkflowRuntime(repository)
    request = EventIngestRequest.model_validate(payload["event"])
    return runtime.process_event(
        payload.get("organisation_id", "demo-org"), payload.get("actor", "worker"), request
    )


@dramatiq.actor(max_retries=3, min_backoff=5_000, max_backoff=120_000)
def sync_gmail_job(payload: dict[str, Any]) -> dict[str, Any]:
    """Poll connected Gmail messages and turn each new message into an idempotent event."""
    from .database import init_db
    from .repository import Repository
    from .runtime import WorkflowRuntime
    from .schemas import EventIngestRequest
    from .tools import DemoToolRegistry

    init_db()
    repository = Repository()
    repository.seed_demo()
    organisation_id = str(payload.get("organisation_id", "demo-org"))
    connection = repository.gmail_connection(organisation_id, include_secret=True)
    if not connection or not connection.get("encrypted_refresh_token"):
        raise RuntimeError("Gmail is not connected for this organisation")

    connector = GmailConnector.from_stored_connection(connection["encrypted_refresh_token"])
    messages = connector.search(
        query=str(payload.get("query", "-label:processed")),
        max_results=int(payload.get("max_results", 20)),
    )
    runtime = WorkflowRuntime(
        repository,
        tool_factory=lambda _org: DemoToolRegistry(gmail_connector=connector),
    )
    runs: list[dict[str, Any]] = []
    for message in messages:
        event = EventIngestRequest(
            event_type="gmail.email_received",
            source="gmail",
            idempotency_key=f"gmail:{message['id']}",
            payload=message,
        )
        runs.append(
            runtime.process_event(organisation_id, str(payload.get("actor", "worker")), event)
        )
    repository.mark_gmail_sync(organisation_id)
    return {"messages_seen": len(messages), "runs": runs}

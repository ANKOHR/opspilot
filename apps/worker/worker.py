from __future__ import annotations

import os
from typing import Any

import dramatiq
from dramatiq.brokers.redis import RedisBroker

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
dramatiq.set_broker(RedisBroker(url=redis_url))


@dramatiq.actor(max_retries=3, min_backoff=5_000, max_backoff=120_000)
def process_event_job(payload: dict[str, Any]) -> dict[str, Any]:
    """Durable queue boundary; the API remains responsive while workers run workflows."""
    from opspilot_api.database import init_db
    from opspilot_api.repository import Repository
    from opspilot_api.runtime import WorkflowRuntime
    from opspilot_api.schemas import EventIngestRequest

    init_db()
    repository = Repository()
    repository.seed_demo()
    runtime = WorkflowRuntime(repository)
    request = EventIngestRequest.model_validate(payload["event"])
    return runtime.process_event(
        payload.get("organisation_id", "demo-org"), payload.get("actor", "worker"), request
    )


if __name__ == "__main__":
    print("OpsPilot worker ready; listening on Redis queue")

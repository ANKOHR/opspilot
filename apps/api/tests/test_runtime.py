from opspilot_api.schemas import ApprovalStatus, EventIngestRequest, RunStatus
from opspilot_api.tools import DemoToolRegistry


def lead_request(key: str) -> EventIngestRequest:
    return EventIngestRequest(
        idempotency_key=key,
        payload={
            "from": "alice@example.com",
            "subject": "Invoice automation",
            "body": "We are a 70-person construction company processing 2,000 invoices each month. Could you show us what you built?",
        },
    )


def test_workflow_pauses_for_approval(runtime):
    engine, _repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("event-1"))
    assert run["status"] == RunStatus.WAITING_FOR_APPROVAL
    assert run["approval_id"]
    assert any(item["event_type"] == "approval.requested" for item in run["trace"])

    completed = engine.decide_approval(
        "demo-org", "tester", run["approval_id"], ApprovalStatus.APPROVED, "Looks good"
    )
    assert completed["status"] == RunStatus.SUCCEEDED
    assert completed["output"]["send"]["sandbox"] is True
    assert any(item["event_type"] == "run.completed" for item in completed["trace"])


def test_duplicate_event_is_idempotent(runtime):
    engine, _ = runtime
    first = engine.process_event("demo-org", "tester", lead_request("same-event"))
    second = engine.process_event("demo-org", "tester", lead_request("same-event"))
    assert first["id"] == second["id"]
    assert second["idempotent_replay"] is True


def test_rejected_approval_stops_external_action(runtime):
    engine, _ = runtime
    run = engine.process_event("demo-org", "tester", lead_request("event-reject"))
    rejected = engine.decide_approval(
        "demo-org",
        "tester",
        run["approval_id"],
        ApprovalStatus.REJECTED,
        "Need a smaller first step",
    )
    assert rejected["status"] == RunStatus.REJECTED
    assert "send" not in (rejected["output"] or {})


def test_checkpoint_replay_creates_new_run(runtime):
    engine, _ = runtime
    original = engine.process_event("demo-org", "tester", lead_request("event-replay"))
    replay = engine.replay("demo-org", "tester", original["id"])
    assert replay["id"] != original["id"]
    assert replay["replay_of"] == original["id"]
    assert replay["status"] == RunStatus.WAITING_FOR_APPROVAL


def test_external_tool_cannot_bypass_approval():
    tools = DemoToolRegistry()
    try:
        tools.execute("gmail.send", {"to": "sandbox@example.com"}, {"gmail.send"})
    except PermissionError as exc:
        assert "requires human approval" in str(exc)
    else:
        raise AssertionError("external tool unexpectedly bypassed approval")

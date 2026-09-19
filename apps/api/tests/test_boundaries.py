from __future__ import annotations

import pytest
from fastapi import HTTPException
from opspilot_api.llm import AnthropicProvider, DemoLLMProvider, OpenAIProvider
from opspilot_api.schemas import (
    ActionClass,
    ApprovalStatus,
    EventIngestRequest,
    LeadQualificationOutput,
    OrganizationContext,
    Role,
    WorkflowStepDefinition,
)
from opspilot_api.security import get_context, require_write
from opspilot_api.tools import DemoToolRegistry
from pydantic import ValidationError


def lead_request(key: str) -> EventIngestRequest:
    return EventIngestRequest(
        idempotency_key=key,
        payload={
            "from": "alice@example.com",
            "subject": "Invoice automation",
            "body": "We are a 70-person construction company processing 2,000 invoices each month.",
        },
    )


def test_waiting_run_contains_typed_lead_and_reviewable_draft(runtime):
    engine, _repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("typed-output"))

    assert run["status"] == "waiting_for_approval"
    assert run["output"]["lead"]["fit_score"] == 94
    assert run["output"]["draft"]["meeting_slots"] == [
        "Tuesday 10:00",
        "Wednesday 14:00",
    ]
    assert run["approval_id"]


def test_approved_run_contains_only_sandbox_side_effects(runtime):
    engine, _repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("sandbox-effects"))
    completed = engine.decide_approval(
        "demo-org", "tester", run["approval_id"], ApprovalStatus.APPROVED, "Approved for demo"
    )

    assert completed["status"] == "succeeded"
    assert completed["output"]["send"]["status"] == "sent_in_sandbox"
    assert completed["output"]["deal"]["sandbox"] is True
    assert completed["output"]["follow_up"]["sandbox"] is True


def test_trace_ordinals_are_monotonic(runtime):
    engine, _repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("ordered-trace"))

    ordinals = [item["ordinal"] for item in run["trace"]]
    assert ordinals == list(range(1, len(ordinals) + 1))


def test_overview_records_waiting_spend_and_completion(runtime):
    engine, repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("overview-metrics"))
    waiting = repository.overview("demo-org")
    assert waiting["runs_today"] == 1
    assert waiting["waiting_approval"] == 1
    assert waiting["ai_spend_usd"] > 0

    engine.decide_approval(
        "demo-org", "tester", run["approval_id"], ApprovalStatus.APPROVED, "Approved"
    )
    completed = repository.overview("demo-org")
    assert completed["success_rate"] == 100.0
    assert completed["waiting_approval"] == 0
    assert completed["average_runtime_seconds"] >= 0


def test_approval_payload_is_explicitly_external_and_sandboxed(runtime):
    engine, repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("approval-payload"))
    approval = repository.approvals("demo-org")[0]

    assert approval["id"] == run["approval_id"]
    assert approval["proposed_action"]["tool"] == "gmail.send"
    assert approval["proposed_action"]["sandbox"] is True
    assert approval["status"] == ApprovalStatus.PENDING


def test_approval_reason_is_persisted_on_rejection(runtime):
    engine, repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("approval-reason"))
    rejected = engine.decide_approval(
        "demo-org", "tester", run["approval_id"], ApprovalStatus.REJECTED, "Need review"
    )

    approval = repository.approvals("demo-org")[0]
    assert rejected["status"] == "rejected"
    assert rejected["error"] == "Need review"
    assert approval["decision_reason"] == "Need review"
    assert approval["status"] == ApprovalStatus.REJECTED


def test_approval_is_one_shot(runtime):
    engine, _repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("one-shot"))
    engine.decide_approval(
        "demo-org", "tester", run["approval_id"], ApprovalStatus.APPROVED, "Approved"
    )

    with pytest.raises(ValueError, match="already been decided"):
        engine.decide_approval(
            "demo-org", "tester", run["approval_id"], ApprovalStatus.REJECTED, "Too late"
        )


def test_replay_preserves_payload_and_gets_new_approval(runtime):
    engine, _repository = runtime
    original = engine.process_event("demo-org", "tester", lead_request("replay-payload"))
    replay = engine.replay("demo-org", "tester", original["id"])

    assert replay["id"] != original["id"]
    assert replay["replay_of"] == original["id"]
    assert replay["payload"] == original["payload"]
    assert replay["approval_id"] != original["approval_id"]


def test_replay_requires_access_to_the_source_organisation(runtime):
    engine, _repository = runtime
    original = engine.process_event("demo-org", "tester", lead_request("replay-isolation"))

    with pytest.raises(KeyError):
        engine.replay("other-org", "tester", original["id"])


def test_provider_failure_marks_run_failed(runtime, monkeypatch):
    engine, repository = runtime

    def fail(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(engine.llm, "generate_structured", fail)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        engine.process_event("demo-org", "tester", lead_request("provider-failure"))

    failed = repository.runs("demo-org")[0]
    assert failed["status"] == "failed"
    assert failed["error"] == "provider unavailable"
    assert failed["trace"][-1]["event_type"] == "run.failed"


def test_unknown_trigger_is_rejected(runtime):
    engine, repository = runtime
    request = EventIngestRequest(
        event_type="unknown.trigger", idempotency_key="unknown-trigger", payload={}
    )

    with pytest.raises(ValueError, match="No active workflow"):
        engine.process_event("demo-org", "tester", request)
    assert repository.runs("demo-org") == []


def test_runs_are_tenant_isolated(runtime):
    engine, repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("run-isolation"))

    assert repository.run_view("other-org", run["id"]) is None
    assert repository.runs("other-org") == []


def test_approvals_are_tenant_isolated(runtime):
    engine, repository = runtime
    run = engine.process_event("demo-org", "tester", lead_request("approval-isolation"))

    assert repository.approvals("other-org") == []
    with pytest.raises(KeyError):
        repository.decide_approval(
            "other-org", run["approval_id"], ApprovalStatus.APPROVED, "Should not work"
        )


def test_workflows_are_tenant_isolated(runtime):
    _engine, repository = runtime

    assert {item["id"] for item in repository.workflows("demo-org")} == {
        "inbound-revenue",
        "ap-exception",
        "support-escalation",
    }
    assert repository.workflows("other-org") == []


@pytest.mark.parametrize(
    ("name", "action_class"),
    [
        ("crm.search_company", ActionClass.READ),
        ("calendar.find_availability", ActionClass.READ),
        ("gmail.create_draft", ActionClass.WRITE),
        ("crm.create_deal", ActionClass.WRITE),
        ("gmail.send", ActionClass.EXTERNAL),
    ],
)
def test_tool_registry_classifies_actions(name, action_class):
    assert DemoToolRegistry().spec(name).action_class == action_class


def test_allowlist_blocks_unlisted_tool():
    with pytest.raises(PermissionError, match="not authorised"):
        DemoToolRegistry().execute("crm.search_company", {}, set())


def test_unknown_tool_is_rejected():
    with pytest.raises(KeyError, match="Unknown tool"):
        DemoToolRegistry().spec("does.not.exist")


def test_write_tool_is_allowed_without_external_approval():
    result = DemoToolRegistry().execute(
        "gmail.create_draft", {}, {"gmail.create_draft"}, approved=False
    )
    assert result["status"] == "created"
    assert result["sandbox"] is True


def test_external_tool_is_allowed_only_after_approval():
    registry = DemoToolRegistry()
    with pytest.raises(PermissionError, match="requires human approval"):
        registry.execute("gmail.send", {}, {"gmail.send"})

    sent = registry.execute("gmail.send", {}, {"gmail.send"}, approved=True)
    assert sent["status"] == "sent_in_sandbox"


def test_demo_provider_returns_valid_lead_schema():
    result = DemoLLMProvider().generate_structured(
        LeadQualificationOutput,
        "extract",
        {"email": {"from": "alice@example.com", "body": "construction"}},
    )
    assert isinstance(result.output, LeadQualificationOutput)
    assert result.output.fit_score == 94
    assert result.provider == "demo"
    assert result.cost_usd > 0


@pytest.mark.parametrize("provider_class", [OpenAIProvider, AnthropicProvider])
def test_live_provider_slots_require_credentials(monkeypatch, provider_class):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = provider_class()

    with pytest.raises(RuntimeError, match="not configured"):
        provider.generate_structured(LeadQualificationOutput, "extract", {})


def test_viewer_role_is_read_only():
    context = OrganizationContext(role=Role.VIEWER)
    with pytest.raises(HTTPException, match="read-only"):
        require_write(context)


@pytest.mark.parametrize("role", [Role.OWNER, Role.ADMIN, Role.OPERATOR])
def test_mutating_roles_are_allowed(role):
    context = OrganizationContext(role=role)
    assert require_write(context) is context


def test_context_defaults_are_safe_demo_values():
    context = get_context(None, None, None)
    assert context.organization_id == "demo-org"
    assert context.user_id == "demo-operator"
    assert context.role == Role.OPERATOR


def test_unknown_role_is_rejected():
    with pytest.raises(HTTPException, match="Unknown role"):
        get_context(x_role="root")


@pytest.mark.parametrize("fit_score", [-1, 101])
def test_lead_schema_rejects_out_of_range_score(fit_score):
    with pytest.raises(ValidationError):
        LeadQualificationOutput(
            company_name="Example",
            need="Automation",
            fit_score=fit_score,
            reasoning=["reason"],
            recommended_action="review",
        )


def test_event_schema_requires_idempotency_key():
    with pytest.raises(ValidationError):
        EventIngestRequest(payload={})


@pytest.mark.parametrize(
    ("field", "value"),
    [("retry_limit", 11), ("timeout_seconds", 0)],
)
def test_workflow_step_schema_rejects_unsafe_bounds(field, value):
    with pytest.raises(ValidationError):
        WorkflowStepDefinition(
            id="step",
            name="Step",
            kind="demo",
            **{field: value},
        )

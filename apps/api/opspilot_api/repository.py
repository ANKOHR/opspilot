from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from .database import SessionLocal
from .models import (
    ApprovalModel,
    AuditLogModel,
    CredentialModel,
    EventModel,
    IntegrationModel,
    OrganizationMemberModel,
    OrganizationModel,
    RunModel,
    TraceModel,
    UsageRecordModel,
    WorkflowModel,
)
from .schemas import ApprovalStatus, RunStatus, WorkflowDefinition


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def as_iso(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class Repository:
    def __init__(self, session_factory: sessionmaker[Session] = SessionLocal) -> None:
        self.session_factory = session_factory

    def seed_demo(self) -> None:
        definitions = [
            WorkflowDefinition(
                id="inbound-revenue",
                name="Inbound Revenue Agent",
                description="Qualifies an inbound enquiry, drafts a response and waits for approval before external action.",
                trigger="gmail.email_received",
                steps=[
                    {"id": "extract", "name": "Extract enquiry", "kind": "llm.structured"},
                    {"id": "crm_lookup", "name": "Search CRM", "kind": "crm.search_company"},
                    {"id": "enrich", "name": "Research company", "kind": "web.company_lookup"},
                    {"id": "score", "name": "Score opportunity", "kind": "llm.structured"},
                    {
                        "id": "calendar",
                        "name": "Find meeting slots",
                        "kind": "calendar.find_availability",
                    },
                    {"id": "draft", "name": "Create response draft", "kind": "gmail.create_draft"},
                    {
                        "id": "approval",
                        "name": "Request human approval",
                        "kind": "human.approval",
                        "requires_approval": True,
                    },
                    {
                        "id": "send",
                        "name": "Send approved response",
                        "kind": "gmail.send",
                        "action_class": "external",
                        "requires_approval": True,
                    },
                    {
                        "id": "deal",
                        "name": "Create CRM deal",
                        "kind": "crm.create_deal",
                        "action_class": "write",
                    },
                    {
                        "id": "follow_up",
                        "name": "Create follow-up task",
                        "kind": "tasks.create_follow_up",
                        "action_class": "write",
                    },
                ],
            ),
            WorkflowDefinition(
                id="ap-exception",
                name="Accounts Payable Exception Agent",
                description="Extracts invoices, applies deterministic approval rules and routes anomalies for review.",
                trigger="invoice.received",
                steps=[
                    {"id": "extract", "name": "Extract invoice", "kind": "llm.structured"},
                    {"id": "validate", "name": "Validate fields", "kind": "deterministic.validate"},
                    {
                        "id": "duplicate",
                        "name": "Check duplicate",
                        "kind": "deterministic.duplicate_check",
                    },
                    {
                        "id": "route",
                        "name": "Route exception",
                        "kind": "human.approval",
                        "requires_approval": True,
                    },
                ],
            ),
            WorkflowDefinition(
                id="support-escalation",
                name="Support Escalation Agent",
                description="Classifies a complaint, retrieves context and routes an appropriate human response.",
                trigger="support.ticket_created",
                steps=[
                    {"id": "classify", "name": "Classify severity", "kind": "llm.structured"},
                    {
                        "id": "retrieve",
                        "name": "Retrieve customer context",
                        "kind": "support.lookup",
                    },
                    {"id": "draft", "name": "Draft response", "kind": "llm.structured"},
                    {
                        "id": "route",
                        "name": "Route to owner",
                        "kind": "human.approval",
                        "requires_approval": True,
                    },
                ],
            ),
        ]
        with self.session_factory() as db:
            org = db.get(OrganizationModel, "demo-org")
            if org is None:
                org = OrganizationModel(id="demo-org", name="Northstar Demo Organisation")
                db.add(org)
                # PostgreSQL enforces the organisation FK immediately. Flush
                # the parent before adding the first membership row so startup
                # behaves the same on SQLite and production Postgres.
                db.flush()
            member = db.scalar(
                select(OrganizationMemberModel).where(
                    OrganizationMemberModel.organisation_id == org.id,
                    OrganizationMemberModel.user_id == "demo-operator",
                )
            )
            if member is None:
                db.add(
                    OrganizationMemberModel(
                        organisation_id="demo-org", user_id="demo-operator", role="operator"
                    )
                )
            for definition in definitions:
                if db.get(WorkflowModel, definition.id) is None:
                    db.add(
                        WorkflowModel(
                            id=definition.id,
                            organisation_id="demo-org",
                            name=definition.name,
                            description=definition.description,
                            trigger_type=definition.trigger,
                            version=definition.version,
                            definition=definition.model_dump(mode="json"),
                        )
                    )
            db.commit()

    def workflows(self, organisation_id: str) -> list[dict[str, Any]]:
        with self.session_factory() as db:
            rows = db.scalars(
                select(WorkflowModel).where(WorkflowModel.organisation_id == organisation_id)
            ).all()
            return [self.workflow_dict(row) for row in rows]

    def workflow_for_trigger(self, organisation_id: str, trigger: str) -> dict[str, Any] | None:
        with self.session_factory() as db:
            row = db.scalar(
                select(WorkflowModel).where(
                    WorkflowModel.organisation_id == organisation_id,
                    WorkflowModel.trigger_type == trigger,
                    WorkflowModel.active.is_(True),
                )
            )
            return self.workflow_dict(row) if row else None

    def workflow_dict(self, row: WorkflowModel) -> dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "trigger": row.trigger_type,
            "version": row.version,
            "definition": row.definition,
        }

    def record_event(
        self, organisation_id: str, event_type: str, key: str, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        with self.session_factory() as db:
            existing = db.scalar(
                select(EventModel).where(
                    EventModel.organisation_id == organisation_id,
                    EventModel.idempotency_key == key,
                )
            )
            if existing:
                return self.event_dict(existing), True
            event = EventModel(
                id=uid("evt"),
                organisation_id=organisation_id,
                event_type=event_type,
                idempotency_key=key,
                payload=payload,
            )
            db.add(event)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                existing = db.scalar(
                    select(EventModel).where(
                        EventModel.organisation_id == organisation_id,
                        EventModel.idempotency_key == key,
                    )
                )
                if existing is None:
                    raise
                return self.event_dict(existing), True
            return self.event_dict(event), False

    def attach_event_run(self, event_id: str, run_id: str) -> None:
        with self.session_factory() as db:
            event = db.get(EventModel, event_id)
            if event:
                event.run_id = run_id
                db.commit()

    def event_dict(self, row: EventModel) -> dict[str, Any]:
        return {
            "id": row.id,
            "run_id": row.run_id,
            "payload": row.payload,
            "event_type": row.event_type,
        }

    def create_run(
        self,
        organisation_id: str,
        workflow: dict[str, Any],
        payload: dict[str, Any],
        replay_of: str | None = None,
    ) -> str:
        run_id = uid("run")
        with self.session_factory() as db:
            db.add(
                RunModel(
                    id=run_id,
                    organisation_id=organisation_id,
                    workflow_id=workflow["id"],
                    workflow_version=workflow["version"],
                    status=RunStatus.RUNNING,
                    trigger_type=workflow["trigger"],
                    payload=payload,
                    current_step=None,
                    replay_of=replay_of,
                )
            )
            db.commit()
        return run_id

    def update_run(self, run_id: str, **changes: Any) -> None:
        with self.session_factory() as db:
            row = db.get(RunModel, run_id)
            if row is None:
                raise KeyError(run_id)
            for key, value in changes.items():
                setattr(row, key, value)
            db.commit()

    def add_trace(self, run_id: str, data: dict[str, Any]) -> None:
        with self.session_factory() as db:
            last = (
                db.scalar(select(func.max(TraceModel.ordinal)).where(TraceModel.run_id == run_id))
                or 0
            )
            db.add(
                TraceModel(
                    run_id=run_id,
                    ordinal=last + 1,
                    event_type=data["event_type"],
                    step_id=data.get("step_id"),
                    status=data.get("status", "completed"),
                    message=data["message"],
                    input_data=data.get("input"),
                    output_data=data.get("output"),
                    latency_ms=data.get("latency_ms"),
                    model=data.get("model"),
                    tool=data.get("tool"),
                    cost_usd=data.get("cost_usd"),
                )
            )
            db.commit()

    def add_usage(self, organisation_id: str, run_id: str, result: Any) -> None:
        with self.session_factory() as db:
            db.add(
                UsageRecordModel(
                    organisation_id=organisation_id,
                    run_id=run_id,
                    provider=result.provider,
                    model=result.model,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=result.cost_usd,
                    latency_ms=result.latency_ms,
                )
            )
            db.commit()

    def create_approval(
        self,
        organisation_id: str,
        run_id: str,
        step_id: str,
        title: str,
        summary: str,
        proposed_action: dict[str, Any],
    ) -> str:
        approval_id = uid("apr")
        with self.session_factory() as db:
            db.add(
                ApprovalModel(
                    id=approval_id,
                    organisation_id=organisation_id,
                    run_id=run_id,
                    step_id=step_id,
                    title=title,
                    summary=summary,
                    proposed_action=proposed_action,
                    status=ApprovalStatus.PENDING,
                )
            )
            db.commit()
        return approval_id

    def decide_approval(
        self, organisation_id: str, approval_id: str, decision: ApprovalStatus, reason: str | None
    ) -> dict[str, Any]:
        with self.session_factory() as db:
            row = db.scalar(
                select(ApprovalModel).where(
                    ApprovalModel.id == approval_id,
                    ApprovalModel.organisation_id == organisation_id,
                )
            )
            if row is None:
                raise KeyError(approval_id)
            if row.status != ApprovalStatus.PENDING:
                raise ValueError("Approval has already been decided")
            row.status = decision
            row.decision_reason = reason
            row.decided_at = datetime.now(UTC)
            db.commit()
            return self.approval_dict(row)

    def approval_dict(self, row: ApprovalModel) -> dict[str, Any]:
        return {
            "id": row.id,
            "run_id": row.run_id,
            "step_id": row.step_id,
            "title": row.title,
            "summary": row.summary,
            "proposed_action": row.proposed_action,
            "status": row.status,
            "created_at": as_iso(row.created_at),
            "decided_at": as_iso(row.decided_at),
            "decision_reason": row.decision_reason,
        }

    def approvals(self, organisation_id: str) -> list[dict[str, Any]]:
        with self.session_factory() as db:
            rows = db.scalars(
                select(ApprovalModel)
                .where(ApprovalModel.organisation_id == organisation_id)
                .order_by(ApprovalModel.created_at.desc())
            ).all()
            return [self.approval_dict(row) for row in rows]

    def run_view(self, organisation_id: str, run_id: str) -> dict[str, Any] | None:
        with self.session_factory() as db:
            row = db.scalar(
                select(RunModel).where(
                    RunModel.id == run_id, RunModel.organisation_id == organisation_id
                )
            )
            if row is None:
                return None
            workflow = db.get(WorkflowModel, row.workflow_id)
            traces = db.scalars(
                select(TraceModel).where(TraceModel.run_id == row.id).order_by(TraceModel.ordinal)
            ).all()
            return {
                "id": row.id,
                "organisation_id": row.organisation_id,
                "workflow_id": row.workflow_id,
                "workflow_name": workflow.name if workflow else row.workflow_id,
                "workflow_version": row.workflow_version,
                "status": row.status,
                "trigger_type": row.trigger_type,
                "payload": row.payload,
                "output": row.output,
                "current_step": row.current_step,
                "error": row.error,
                "approval_id": row.approval_id,
                "replay_of": row.replay_of,
                "started_at": as_iso(row.started_at),
                "updated_at": as_iso(row.updated_at),
                "completed_at": as_iso(row.completed_at),
                "trace": [
                    {
                        "id": item.id,
                        "ordinal": item.ordinal,
                        "event_type": item.event_type,
                        "step_id": item.step_id,
                        "status": item.status,
                        "message": item.message,
                        "input": item.input_data,
                        "output": item.output_data,
                        "latency_ms": item.latency_ms,
                        "model": item.model,
                        "tool": item.tool,
                        "cost_usd": item.cost_usd,
                        "created_at": as_iso(item.created_at),
                    }
                    for item in traces
                ],
            }

    def runs(self, organisation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.session_factory() as db:
            rows = db.scalars(
                select(RunModel)
                .where(RunModel.organisation_id == organisation_id)
                .order_by(RunModel.started_at.desc())
                .limit(limit)
            ).all()
            return [self.run_view(organisation_id, row.id) for row in rows]  # type: ignore[misc]

    def audit(self, organisation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self.session_factory() as db:
            rows = db.scalars(
                select(AuditLogModel)
                .where(AuditLogModel.organisation_id == organisation_id)
                .order_by(AuditLogModel.created_at.desc())
                .limit(limit)
            ).all()
            return [
                {
                    "actor": row.actor,
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id,
                    "metadata": row.metadata_json,
                    "created_at": as_iso(row.created_at),
                }
                for row in rows
            ]

    def add_audit(
        self,
        organisation_id: str,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.session_factory() as db:
            db.add(
                AuditLogModel(
                    organisation_id=organisation_id,
                    actor=actor,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    metadata_json=metadata,
                )
            )
            db.commit()

    def upsert_gmail_connection(
        self,
        organisation_id: str,
        external_account: str,
        scopes: list[str],
        encrypted_refresh_token: str,
    ) -> dict[str, Any]:
        integration_id = f"gmail_{organisation_id}"
        credential_id = f"credential_{integration_id}"
        with self.session_factory() as db:
            integration = db.get(IntegrationModel, integration_id)
            if integration is None:
                integration = IntegrationModel(
                    id=integration_id,
                    organisation_id=organisation_id,
                    provider="gmail",
                )
                db.add(integration)
            integration.status = "connected"
            integration.scopes = scopes
            integration.external_account = external_account

            credential = db.get(CredentialModel, credential_id)
            if credential is None:
                credential = CredentialModel(
                    id=credential_id,
                    integration_id=integration_id,
                    encrypted_refresh_token=encrypted_refresh_token,
                )
                db.add(credential)
            else:
                credential.encrypted_refresh_token = encrypted_refresh_token
                credential.rotated_at = datetime.now(UTC)
            db.commit()
            return self.integration_dict(integration)

    def gmail_connection(
        self, organisation_id: str, include_secret: bool = False
    ) -> dict[str, Any] | None:
        with self.session_factory() as db:
            integration = db.scalar(
                select(IntegrationModel).where(
                    IntegrationModel.organisation_id == organisation_id,
                    IntegrationModel.provider == "gmail",
                )
            )
            if integration is None:
                return None
            result = self.integration_dict(integration)
            if include_secret:
                credential = db.scalar(
                    select(CredentialModel).where(
                        CredentialModel.integration_id == integration.id,
                    )
                )
                result["encrypted_refresh_token"] = (
                    credential.encrypted_refresh_token if credential else None
                )
            return result

    def integration_dict(self, row: IntegrationModel) -> dict[str, Any]:
        return {
            "id": row.id,
            "provider": row.provider,
            "status": row.status,
            "scopes": row.scopes or [],
            "external_account": row.external_account,
            "last_sync_at": as_iso(row.last_sync_at),
        }

    def mark_gmail_sync(self, organisation_id: str) -> None:
        with self.session_factory() as db:
            integration = db.scalar(
                select(IntegrationModel).where(
                    IntegrationModel.organisation_id == organisation_id,
                    IntegrationModel.provider == "gmail",
                )
            )
            if integration:
                integration.last_sync_at = datetime.now(UTC)
                db.commit()

    def overview(self, organisation_id: str) -> dict[str, Any]:
        with self.session_factory() as db:
            rows = db.scalars(
                select(RunModel).where(RunModel.organisation_id == organisation_id)
            ).all()
            approvals = db.scalars(
                select(ApprovalModel).where(
                    ApprovalModel.organisation_id == organisation_id,
                    ApprovalModel.status == ApprovalStatus.PENDING,
                )
            ).all()
            usage = db.scalars(
                select(UsageRecordModel).where(UsageRecordModel.organisation_id == organisation_id)
            ).all()
            successes = sum(row.status == RunStatus.SUCCEEDED for row in rows)
            failures = sum(row.status in (RunStatus.FAILED, RunStatus.REJECTED) for row in rows)
            durations = [
                (row.completed_at - row.started_at).total_seconds()
                for row in rows
                if row.completed_at is not None and row.started_at is not None
            ]
            active = (
                db.scalar(
                    select(func.count(WorkflowModel.id)).where(
                        WorkflowModel.organisation_id == organisation_id,
                        WorkflowModel.active.is_(True),
                    )
                )
                or 0
            )
            return {
                "runs_today": len(rows),
                "success_rate": round((successes / len(rows)) * 100, 1) if rows else 0,
                "waiting_approval": len(approvals),
                "failures": failures,
                "ai_spend_usd": round(sum(item.cost_usd for item in usage), 4),
                "average_runtime_seconds": round(sum(durations) / len(durations), 1)
                if durations
                else 0,
                "active_workflows": active,
            }

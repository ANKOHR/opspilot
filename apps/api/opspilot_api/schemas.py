from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    STOPPED_BY_POLICY = "stopped_by_policy"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ActionClass(StrEnum):
    READ = "read"
    WRITE = "write"
    EXTERNAL = "external"
    DESTRUCTIVE = "destructive"


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class OrganizationContext(BaseModel):
    organization_id: str = "demo-org"
    user_id: str = "demo-operator"
    role: Role = Role.OPERATOR


class WorkflowStepDefinition(BaseModel):
    id: str
    name: str
    kind: str
    action_class: ActionClass = ActionClass.READ
    requires_approval: bool = False
    retry_limit: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=60, ge=1, le=900)


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    version: int = 1
    steps: list[WorkflowStepDefinition]


class EventIngestRequest(BaseModel):
    event_type: str = "gmail.email_received"
    idempotency_key: str
    source: str = "demo-gmail"
    payload: dict[str, Any]


class ApprovalDecision(BaseModel):
    decision: ApprovalStatus
    reason: str | None = None


class LeadQualificationOutput(BaseModel):
    company_name: str
    contact_name: str | None = None
    contact_email: str | None = None
    company_size: int | None = None
    need: str
    budget_signal: str | None = None
    fit_score: int = Field(ge=0, le=100)
    reasoning: list[str]
    recommended_action: str


class DraftResponseOutput(BaseModel):
    subject: str
    body: str
    meeting_slots: list[str]


class TraceEvent(BaseModel):
    id: int | None = None
    ordinal: int
    event_type: str
    step_id: str | None = None
    status: str
    message: str
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    latency_ms: float | None = None
    model: str | None = None
    tool: str | None = None
    cost_usd: float | None = None
    created_at: datetime | None = None


class ApprovalView(BaseModel):
    id: str
    run_id: str
    step_id: str
    title: str
    summary: str
    proposed_action: dict[str, Any]
    status: ApprovalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decision_reason: str | None = None


class RunView(BaseModel):
    id: str
    organisation_id: str
    workflow_id: str
    workflow_name: str
    workflow_version: int
    status: RunStatus
    trigger_type: str
    payload: dict[str, Any]
    output: dict[str, Any] | None = None
    current_step: str | None = None
    error: str | None = None
    approval_id: str | None = None
    replay_of: str | None = None
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    trace: list[TraceEvent] = Field(default_factory=list)


class OverviewView(BaseModel):
    runs_today: int
    success_rate: float
    waiting_approval: int
    failures: int
    ai_spend_usd: float
    average_runtime_seconds: float
    active_workflows: int

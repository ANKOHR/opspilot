from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .repository import Repository
from .runtime import WorkflowRuntime
from .schemas import (
    ApprovalDecision,
    EventIngestRequest,
    OrganizationContext,
    OverviewView,
    RunView,
)
from .security import get_context, require_write

repository = Repository()
runtime = WorkflowRuntime(repository)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    repository.seed_demo()
    yield


app = FastAPI(
    title="OpsPilot API",
    version="0.1.0",
    description="Auditable human-supervised AI operations runtime",
    lifespan=lifespan,
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "API_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "opspilot-api", "mode": "sandbox"}


@app.get("/api/overview", response_model=OverviewView)
def overview(context: OrganizationContext = Depends(get_context)) -> dict:
    return repository.overview(context.organization_id)


@app.get("/api/workflows")
def workflows(context: OrganizationContext = Depends(get_context)) -> list[dict]:
    return repository.workflows(context.organization_id)


@app.get("/api/runs")
def runs(context: OrganizationContext = Depends(get_context)) -> list[dict]:
    return repository.runs(context.organization_id)


@app.get("/api/runs/{run_id}", response_model=RunView)
def run_detail(run_id: str, context: OrganizationContext = Depends(get_context)) -> dict:
    result = repository.run_view(context.organization_id, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@app.get("/api/approvals")
def approvals(context: OrganizationContext = Depends(get_context)) -> list[dict]:
    return repository.approvals(context.organization_id)


@app.get("/api/audit")
def audit(context: OrganizationContext = Depends(get_context)) -> list[dict]:
    return repository.audit(context.organization_id)


@app.post("/api/events", response_model=RunView)
def ingest_event(
    request: EventIngestRequest, context: OrganizationContext = Depends(get_context)
) -> dict:
    require_write(context)
    try:
        return runtime.process_event(context.organization_id, context.user_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/demo/inbound-lead", response_model=RunView)
def run_demo(context: OrganizationContext = Depends(get_context)) -> dict:
    require_write(context)
    request = EventIngestRequest(
        idempotency_key="demo-gmail-message-1948837284",
        payload={
            "from": "alice@example.com",
            "subject": "Invoice automation for our construction business",
            "body": "Hi, we are a 70-person construction company processing roughly 2,000 invoices per month. Could somebody show us what you have built?",
        },
    )
    try:
        return runtime.process_event(context.organization_id, context.user_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/approvals/{approval_id}/decision", response_model=RunView)
def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    context: OrganizationContext = Depends(get_context),
) -> dict:
    require_write(context)
    try:
        return runtime.decide_approval(
            context.organization_id,
            context.user_id,
            approval_id,
            decision.decision,
            decision.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Approval not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/runs/{run_id}/replay", response_model=RunView)
def replay_run(run_id: str, context: OrganizationContext = Depends(get_context)) -> dict:
    require_write(context)
    try:
        return runtime.replay(context.organization_id, context.user_id, run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

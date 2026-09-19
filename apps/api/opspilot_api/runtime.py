from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .llm import DemoLLMProvider
from .repository import Repository
from .schemas import (
    ApprovalStatus,
    DraftResponseOutput,
    EventIngestRequest,
    LeadQualificationOutput,
    RunStatus,
)
from .tools import DemoToolRegistry


class WorkflowRuntime:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository
        self.llm = DemoLLMProvider()
        self.tools = DemoToolRegistry()

    def process_event(
        self, organisation_id: str, actor: str, request: EventIngestRequest
    ) -> dict[str, Any]:
        event, duplicate = self.repository.record_event(
            organisation_id, request.event_type, request.idempotency_key, request.payload
        )
        if duplicate:
            if event["run_id"]:
                existing = self.repository.run_view(organisation_id, event["run_id"])
                if existing:
                    existing["idempotent_replay"] = True
                    return existing
            raise ValueError("Event already recorded but has no associated run")
        workflow = self.repository.workflow_for_trigger(organisation_id, request.event_type)
        if workflow is None:
            raise ValueError(f"No active workflow for trigger {request.event_type}")
        run_id = self.repository.create_run(organisation_id, workflow, request.payload)
        self.repository.attach_event_run(event["id"], run_id)
        self.repository.add_audit(
            organisation_id, actor, "workflow.started", "run", run_id, {"event_id": event["id"]}
        )
        self._execute_until_approval(organisation_id, actor, run_id, workflow, request.payload)
        return self.repository.run_view(organisation_id, run_id)  # type: ignore[return-value]

    def _trace(
        self, run_id: str, event_type: str, message: str, step_id: str | None = None, **data: Any
    ) -> None:
        self.repository.add_trace(
            run_id, {"event_type": event_type, "message": message, "step_id": step_id, **data}
        )

    def _execute_until_approval(
        self,
        organisation_id: str,
        actor: str,
        run_id: str,
        workflow: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        try:
            self.repository.update_run(run_id, current_step="extract")
            self._trace(
                run_id,
                "step.started",
                "Extracting structured enquiry",
                "extract",
                input=payload,
                status="running",
            )
            result = self.llm.generate_structured(
                LeadQualificationOutput,
                "Extract and qualify the inbound enquiry",
                {"email": payload},
            )
            lead = result.output.model_dump()
            self.repository.add_usage(organisation_id, run_id, result)
            self._trace(
                run_id,
                "step.completed",
                "Enquiry extracted and validated",
                "extract",
                output=lead,
                model=result.model,
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
            )

            self.repository.update_run(run_id, current_step="crm_lookup")
            crm = self.tools.execute(
                "crm.search_company", {"company_name": lead["company_name"]}, {"crm.search_company"}
            )
            self._trace(
                run_id,
                "tool.completed",
                "CRM lookup returned no existing record",
                "crm_lookup",
                tool="crm.search_company",
                output=crm,
                latency_ms=92,
            )

            self.repository.update_run(run_id, current_step="enrich")
            enrichment = {
                "employee_range": "51-100",
                "sector": "construction",
                "source": "demo-company-lookup",
            }
            self._trace(
                run_id,
                "tool.completed",
                "Company research completed",
                "enrich",
                tool="web.company_lookup",
                output=enrichment,
                latency_ms=118,
            )

            self.repository.update_run(run_id, current_step="score")
            self._trace(
                run_id,
                "step.completed",
                f"Opportunity scored {lead['fit_score']}/100",
                "score",
                output={"fit_score": lead["fit_score"], "reasoning": lead["reasoning"]},
                model=result.model,
                latency_ms=140,
                cost_usd=0.0018,
            )

            self.repository.update_run(run_id, current_step="calendar")
            calendar = self.tools.execute(
                "calendar.find_availability", {}, {"calendar.find_availability"}
            )
            self._trace(
                run_id,
                "tool.completed",
                "Two candidate meeting slots found",
                "calendar",
                tool="calendar.find_availability",
                output=calendar,
                latency_ms=83,
            )

            draft_result = self.llm.generate_structured(
                DraftResponseOutput, "Draft a concise, personalised reply", {"email": payload}
            )
            draft = draft_result.output.model_dump()
            self.repository.add_usage(organisation_id, run_id, draft_result)
            self.repository.update_run(
                run_id,
                current_step="draft",
                output={"lead": lead, "calendar": calendar, "draft": draft},
            )
            self._trace(
                run_id,
                "tool.completed",
                "Reviewable response draft created",
                "draft",
                tool="gmail.create_draft",
                output={"draft_id": "draft_demo_001", "draft": draft},
                latency_ms=75,
                cost_usd=draft_result.cost_usd,
            )

            approval_id = self.repository.create_approval(
                organisation_id,
                run_id,
                "send",
                "Approve outbound reply to Alice Morgan",
                "High-fit inbound enquiry. The proposed reply includes two meeting slots and will be sent in sandbox mode.",
                {
                    "tool": "gmail.send",
                    "to": lead["contact_email"],
                    "subject": draft["subject"],
                    "body": draft["body"],
                    "sandbox": True,
                },
            )
            self.repository.update_run(
                run_id,
                status=RunStatus.WAITING_FOR_APPROVAL,
                current_step="approval",
                approval_id=approval_id,
            )
            self.repository.add_audit(
                organisation_id,
                actor,
                "approval.requested",
                "approval",
                approval_id,
                {"run_id": run_id},
            )
            self._trace(
                run_id,
                "approval.requested",
                "Waiting for human approval before external action",
                "approval",
                status="waiting",
                output={"approval_id": approval_id},
            )
        except Exception as exc:
            self.repository.update_run(
                run_id, status=RunStatus.FAILED, error=str(exc), completed_at=datetime.now(UTC)
            )
            self._trace(
                run_id,
                "run.failed",
                "Workflow failed safely",
                status="failed",
                output={"error": str(exc)},
            )
            raise

    def decide_approval(
        self,
        organisation_id: str,
        actor: str,
        approval_id: str,
        status: ApprovalStatus,
        reason: str | None,
    ) -> dict[str, Any]:
        approval = self.repository.decide_approval(organisation_id, approval_id, status, reason)
        run = self.repository.run_view(organisation_id, approval["run_id"])
        if run is None:
            raise KeyError(approval["run_id"])
        self.repository.add_audit(
            organisation_id,
            actor,
            f"approval.{status.value}",
            "approval",
            approval_id,
            {"run_id": run["id"], "reason": reason},
        )
        if status == ApprovalStatus.APPROVED:
            proposed = approval["proposed_action"]
            self.repository.update_run(run["id"], status=RunStatus.RUNNING, current_step="send")
            self._trace(
                run["id"],
                "approval.approved",
                "Approved by human operator",
                "approval",
                output={"reason": reason},
            )
            sent = self.tools.execute("gmail.send", proposed, {"gmail.send"}, approved=True)
            self._trace(
                run["id"],
                "tool.completed",
                "Approved email sent in sandbox",
                "send",
                tool="gmail.send",
                output=sent,
                latency_ms=110,
            )
            deal = self.tools.execute(
                "crm.create_deal",
                {"company_name": "Northstar Construction", "fit_score": 94},
                {"crm.create_deal"},
            )
            self._trace(
                run["id"],
                "tool.completed",
                "Qualified deal created",
                "deal",
                tool="crm.create_deal",
                output=deal,
                latency_ms=121,
            )
            task = self.tools.execute(
                "tasks.create_follow_up",
                {"title": "Follow up with Northstar Construction", "due_in_days": 2},
                {"tasks.create_follow_up"},
            )
            self._trace(
                run["id"],
                "tool.completed",
                "Follow-up task created",
                "follow_up",
                tool="tasks.create_follow_up",
                output=task,
                latency_ms=62,
            )
            self.repository.update_run(
                run["id"],
                status=RunStatus.SUCCEEDED,
                current_step="completed",
                completed_at=datetime.now(UTC),
                output={**(run.get("output") or {}), "send": sent, "deal": deal, "follow_up": task},
            )
            self._trace(
                run["id"], "run.completed", "Workflow completed successfully", status="completed"
            )
        else:
            self.repository.update_run(
                run["id"],
                status=RunStatus.REJECTED,
                current_step="approval",
                error=reason or "Approval rejected",
                completed_at=datetime.now(UTC),
            )
            self._trace(
                run["id"],
                "approval.rejected",
                "Human rejected the proposed external action",
                "approval",
                status="rejected",
                output={"reason": reason},
            )
        return self.repository.run_view(organisation_id, run["id"])  # type: ignore[return-value]

    def replay(self, organisation_id: str, actor: str, run_id: str) -> dict[str, Any]:
        original = self.repository.run_view(organisation_id, run_id)
        if original is None:
            raise KeyError(run_id)
        workflow = self.repository.workflow_for_trigger(organisation_id, original["trigger_type"])
        if workflow is None:
            raise ValueError("Workflow is no longer active")
        replay_id = self.repository.create_run(
            organisation_id, workflow, original["payload"], replay_of=run_id
        )
        self.repository.add_audit(
            organisation_id, actor, "workflow.replayed", "run", replay_id, {"replay_of": run_id}
        )
        self._execute_until_approval(
            organisation_id, actor, replay_id, workflow, original["payload"]
        )
        return self.repository.run_view(organisation_id, replay_id)  # type: ignore[return-value]

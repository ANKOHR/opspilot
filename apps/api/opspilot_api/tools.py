from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .schemas import ActionClass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    action_class: ActionClass
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class DemoToolRegistry:
    """Sandbox connectors. External actions are recorded as simulated side effects."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {
            "crm.search_company": ToolSpec(
                "crm.search_company",
                "Search the CRM for an existing company",
                ActionClass.READ,
                self.search_company,
            ),
            "calendar.find_availability": ToolSpec(
                "calendar.find_availability",
                "Find candidate meeting slots",
                ActionClass.READ,
                self.find_availability,
            ),
            "gmail.create_draft": ToolSpec(
                "gmail.create_draft",
                "Create a reviewable email draft",
                ActionClass.WRITE,
                self.create_draft,
            ),
            "crm.create_deal": ToolSpec(
                "crm.create_deal",
                "Create a qualified CRM deal",
                ActionClass.WRITE,
                self.create_deal,
            ),
            "tasks.create_follow_up": ToolSpec(
                "tasks.create_follow_up",
                "Create an internal follow-up task",
                ActionClass.WRITE,
                self.create_follow_up,
            ),
            "gmail.send": ToolSpec(
                "gmail.send",
                "Send an email to an external recipient",
                ActionClass.EXTERNAL,
                self.send_email,
            ),
        }

    def spec(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        allowed: set[str],
        approved: bool = False,
    ) -> dict[str, Any]:
        if name not in allowed:
            raise PermissionError(f"Tool {name} is not authorised for this workflow")
        spec = self.spec(name)
        if spec.action_class in (ActionClass.EXTERNAL, ActionClass.DESTRUCTIVE) and not approved:
            raise PermissionError(f"Tool {name} requires human approval before execution")
        return spec.handler(arguments)

    def search_company(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "found": False,
            "company_name": arguments.get("company_name", "Northstar Construction"),
            "reason": "No existing demo CRM record found",
        }

    def find_availability(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"slots": ["Tuesday 10:00", "Wednesday 14:00"], "timezone": "Europe/London"}

    def create_draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"draft_id": "draft_demo_001", "status": "created", "sandbox": True}

    def create_deal(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"deal_id": "deal_demo_001", "status": "created", "sandbox": True}

    def create_follow_up(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"task_id": "task_demo_001", "status": "created", "sandbox": True}

    def send_email(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"message_id": "sandbox_message_001", "status": "sent_in_sandbox", "sandbox": True}

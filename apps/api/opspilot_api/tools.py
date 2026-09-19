from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .gmail import GmailConnector
from .schemas import ActionClass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    action_class: ActionClass
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class DemoToolRegistry:
    """Connector registry with a deterministic sandbox and optional live Gmail adapter."""

    def __init__(self, gmail_connector: GmailConnector | None = None) -> None:
        self.gmail_connector = gmail_connector
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
            "gmail.search": ToolSpec(
                "gmail.search",
                "Search messages in the connected Gmail account",
                ActionClass.READ,
                self.search_gmail,
            ),
            "gmail.read": ToolSpec(
                "gmail.read",
                "Read a message from the connected Gmail account",
                ActionClass.READ,
                self.read_gmail,
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

    @property
    def live_gmail(self) -> bool:
        return self.gmail_connector is not None

    def search_company(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "found": False,
            "company_name": arguments.get("company_name", "Northstar Construction"),
            "reason": "No existing demo CRM record found",
        }

    def find_availability(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"slots": ["Tuesday 10:00", "Wednesday 14:00"], "timezone": "Europe/London"}

    def create_draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.gmail_connector:
            return self.gmail_connector.create_draft(
                to=str(arguments["to"]),
                subject=str(arguments["subject"]),
                body=str(arguments["body"]),
                thread_id=arguments.get("thread_id"),
            )
        return {"draft_id": "draft_demo_001", "status": "created", "sandbox": True}

    def search_gmail(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.gmail_connector:
            return {
                "messages": self.gmail_connector.search(
                    query=str(arguments.get("query", "")),
                    max_results=int(arguments.get("max_results", 20)),
                ),
                "provider": "gmail",
                "external": True,
            }
        return {"messages": [], "provider": "demo", "sandbox": True}

    def read_gmail(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.gmail_connector:
            return self.gmail_connector.read(str(arguments["message_id"]))
        return {
            "id": arguments.get("message_id", "sandbox_message_001"),
            "body": "Sandbox message content",
            "provider": "demo",
            "sandbox": True,
        }

    def create_deal(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"deal_id": "deal_demo_001", "status": "created", "sandbox": True}

    def create_follow_up(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"task_id": "task_demo_001", "status": "created", "sandbox": True}

    def send_email(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.gmail_connector:
            return self.gmail_connector.send(**arguments)
        return {"message_id": "sandbox_message_001", "status": "sent_in_sandbox", "sandbox": True}

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

from .schemas import DraftResponseOutput, LeadQualificationOutput

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResult(Generic[T]):
    output: T
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float


class LLMProvider(Protocol):
    def generate_structured(
        self, schema: type[T], prompt: str, context: dict[str, Any]
    ) -> LLMResult[T]: ...


class DemoLLMProvider:
    """Deterministic provider used by the sandbox/demo and test suite.

    It deliberately returns validated Pydantic models, allowing the rest of the
    runtime to exercise schema, trace, cost and approval behavior without keys.
    """

    provider = "demo"
    model = "deterministic-ops-0"

    def generate_structured(
        self, schema: type[T], prompt: str, context: dict[str, Any]
    ) -> LLMResult[T]:
        email = context.get("email", {})
        body = str(email.get("body", ""))
        company = "Northstar Construction"
        contact = "Alice Morgan"
        if "construction" in body.lower():
            company = "Northstar Construction"
        if "alice" in body.lower():
            contact = "Alice Morgan"
        if schema is LeadQualificationOutput:
            result: BaseModel = LeadQualificationOutput(
                company_name=company,
                contact_name=contact,
                contact_email=email.get("from", "alice@example.com"),
                company_size=70,
                need="Invoice processing automation",
                budget_signal="Explicit evaluation request with meaningful operational volume",
                fit_score=94,
                reasoning=[
                    "Clear automation need",
                    "Meaningful monthly invoice volume",
                    "Established operating team",
                    "Explicit purchase intent",
                ],
                recommended_action="Create a qualified deal and propose a discovery call",
            )
        elif schema is DraftResponseOutput:
            result = DraftResponseOutput(
                subject="Re: Invoice automation for Northstar Construction",
                body=(
                    f"Hi {contact},\n\nThanks for reaching out. Your invoice volume sounds like a strong "
                    "fit for an automation discovery session. I can show you how the workflow handles "
                    "extraction, validation and exception routing.\n\nWould either Tuesday at 10:00 or "
                    "Wednesday at 14:00 work?\n\nBest,\nHenry"
                ),
                meeting_slots=["Tuesday 10:00", "Wednesday 14:00"],
            )
        else:
            result = schema.model_validate({})
        return LLMResult(
            output=result,  # type: ignore[arg-type]
            provider=self.provider,
            model=self.model,
            input_tokens=max(40, len(prompt) // 4),
            output_tokens=max(60, len(result.model_dump_json()) // 4),
            latency_ms=140.0,
            cost_usd=0.0018,
        )


class OpenAIProvider:
    """Provider boundary for a real structured-output adapter.

    The local build never calls this class unless explicitly configured. Keeping
    it behind the same protocol lets workflow definitions choose a provider later.
    """

    provider = "openai"

    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate_structured(
        self, schema: type[T], prompt: str, context: dict[str, Any]
    ) -> LLMResult[T]:
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured; use DemoLLMProvider for local runs"
            )
        raise NotImplementedError(
            "Connect the provider SDK here; the demo deliberately stays key-free"
        )


class AnthropicProvider:
    provider = "anthropic"

    def __init__(self, model: str = "claude-3-5-haiku-latest") -> None:
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def generate_structured(
        self, schema: type[T], prompt: str, context: dict[str, Any]
    ) -> LLMResult[T]:
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not configured; use DemoLLMProvider for local runs"
            )
        raise NotImplementedError(
            "Connect the provider SDK here; the demo deliberately stays key-free"
        )

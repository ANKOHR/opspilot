from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
DATASET = ROOT / "dataset.jsonl"


def build_cases(count: int = 100) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for index in range(count):
        high_intent = index % 4 != 3
        volume = 2000 + index * 13 if high_intent else 120 + index
        body = (
            f"We are a 70-person construction company processing {volume} invoices each month. "
            "We are evaluating automation and would like a product demonstration."
            if high_intent
            else f"We are researching invoice tools for a small team of {volume} invoices each month."
        )
        cases.append(
            {
                "id": f"lead-{index + 1:03d}",
                "text": body,
                "expected": {
                    "intent": "sales_enquiry",
                    "fit_band": "high" if high_intent else "medium",
                    "requires_approval": True,
                },
            }
        )
    return cases


def write_dataset() -> None:
    DATASET.write_text(
        "\n".join(json.dumps(case) for case in build_cases()) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    write_dataset()
    print(f"wrote {DATASET}")

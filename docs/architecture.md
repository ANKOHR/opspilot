# OpsPilot architecture

OpsPilot is an event-driven workflow platform for human-supervised business automation.

```text
Next.js dashboard
        |
FastAPI API  ----  Postgres
        |                 |
Redis queue  ----  worker/runtime
        |
provider + connector adapters
```

The runtime stores an incoming event before dispatching work. A unique
`(organisation_id, idempotency_key)` constraint prevents duplicate triggers. Each run references
an immutable workflow version and writes an ordered trace of model calls, tool calls, approvals,
latency, and estimated cost.

The local demo uses SQLite and deterministic sandbox adapters so it is runnable without secrets.
Docker Compose switches the persistence and queue services to Postgres and Redis. The provider
boundary supports a deterministic local provider plus explicit OpenAI and Anthropic adapter
slots.

LLMs are used for interpretation, extraction, classification and drafting. Permissions, threshold
rules, state transitions, budgets and approval gates stay deterministic in Python.


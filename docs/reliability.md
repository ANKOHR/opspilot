# Reliability model

The platform is designed around explicit failure boundaries:

1. Record the event before queueing.
2. Use a unique idempotency key per source event.
3. Keep workflow state and traces durable.
4. Retry transient queue work with bounded exponential backoff.
5. Stop on policy budget, schema or permission failures.
6. Pause at approvals rather than guessing.
7. Replay from a recorded checkpoint or from the original event.

The included worker uses Dramatiq and Redis with three retries. Gmail sync is queued through the
same worker boundary and turns each provider message id into an idempotency key. The API's local
synchronous event path keeps the demo easy to run; a production webhook handler should enqueue
`process_event_job` and return immediately.

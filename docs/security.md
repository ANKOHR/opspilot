# Security and control model

- Every read and write is scoped by `organisation_id`.
- The demo exposes a development context through `X-Organization-ID`, `X-User-ID` and `X-Role`.
  Replace this boundary with signed session/JWT validation before production use.
- Roles are `owner`, `admin`, `operator` and `viewer`; viewers cannot ingest events, approve actions
  or replay runs.
- Tool metadata classifies actions as read, write, external or destructive.
- External actions require an approval record. The local Gmail adapter can only produce a
  `sent_in_sandbox` result.
- Integration credentials belong server-side and should be encrypted at rest. They are never part
  of the browser payload or trace.
- Audit logs record workflow starts, approval requests/decisions and replay operations.
- Rate limiting, secret rotation, provider allow-lists and real OAuth consent are deployment gates,
  not silently implied by the local demo.


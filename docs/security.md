# Security and control model

- Every read and write is scoped by `organisation_id`.
- The demo exposes a development context through `X-Organization-ID`, `X-User-ID` and `X-Role`.
  Replace this boundary with signed session/JWT validation before production use.
- Roles are `owner`, `admin`, `operator` and `viewer`; viewers cannot ingest events, approve actions
  or replay runs.
- Tool metadata classifies actions as read, write, external or destructive.
- External actions require an approval record. The default Gmail adapter produces a
  `sent_in_sandbox` result; a connected Gmail OAuth adapter can send only after that same approval
  gate is satisfied.
- Gmail refresh credentials belong server-side and are encrypted with Fernet before persistence.
  They are never part of the browser payload or trace. OAuth state is signed and expires after ten
  minutes.
- Audit logs record workflow starts, approval requests/decisions and replay operations.
- Rate limiting, secret rotation, provider allow-lists and production session authentication remain
  deployment gates, not silently implied by the local demo. The current demo identity boundary is
  the existing development header context.

# External proof release checklist

This checklist is intentionally separate from the local verification record. A green local build
does not prove that a public repository, hosted deployment or live OAuth flow exists.

## Public repository

- [x] Confirm the exact Git hosting target and repository name: public `ANKOHR/opspilot`.
- [x] Scan the tree for secrets and remove local databases, logs and generated caches from the
      publication set.
- [x] Keep `.env.example`, the architecture diagram, setup instructions and the synthetic-eval
      disclaimer in the published tree.
- [ ] Add committed UI screenshots only after capturing them from the local dashboard and checking
      that they contain no private data.
- [ ] Re-run `scripts/verify.ps1` from a clean checkout before describing the repository as
      reproducible.

## Hosted demo

- [x] Confirm the exact hosting account and target: Vercel `opspilot-web` plus Railway project
      `opspilot`.
- [x] Configure a seeded demo workspace with sandbox adapters and a visible sandbox label.
- [ ] Add demo authentication or a deliberately read-only public surface before exposing it.
- [x] Verify API, worker, Postgres and Redis health from outside the development machine.
- [x] Record the public URL and deployment revision as evidence.

## One real integration

- [x] Choose one connector: Gmail.
- [x] Confirm the authorized test account/workspace and OAuth redirect URI.
- [x] Store refresh credentials server-side only and document the scopes.
- [x] Run one approved, reversible end-to-end action in the test workspace.
- [x] Preserve provider response evidence and distinguish an attempted action from a confirmed
      provider-side result.

## Demo and CV

- [ ] Record a 60–90 second flow: trigger, approval pause, approval, completion, audit trace and
      analytics.
- [x] Use the synthetic qualifier beside every evaluation result.
- [ ] Put the project on the CV with the measured local claims; do not claim deployment, OAuth or
      customer outcomes until the corresponding evidence exists.

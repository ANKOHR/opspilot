# External proof release checklist

This checklist is intentionally separate from the local verification record. A green local build
does not prove that a public repository, hosted deployment or live OAuth flow exists.

## Public repository

- [ ] Confirm the exact Git hosting target and repository name.
- [ ] Scan the tree for secrets and remove local databases, logs and generated caches from the
      publication set.
- [ ] Keep `.env.example`, the architecture diagram, setup instructions and the synthetic-eval
      disclaimer in the published tree.
- [ ] Add committed UI screenshots only after capturing them from the local dashboard and checking
      that they contain no private data.
- [ ] Re-run `scripts/verify.ps1` from a clean checkout before describing the repository as
      reproducible.

## Hosted demo

- [ ] Confirm the exact hosting account and target (for example, Vercel plus a named API host).
- [ ] Configure a seeded demo workspace with sandbox adapters and a visible sandbox label.
- [ ] Add demo authentication or a deliberately read-only public surface before exposing it.
- [ ] Verify API, worker, Postgres and Redis health from outside the development machine.
- [ ] Record the public URL and deployment revision as evidence.

## One real integration

- [ ] Choose one connector: Gmail or HubSpot.
- [ ] Confirm the exact test account/workspace and OAuth redirect URI.
- [ ] Store refresh credentials server-side only and document the scopes.
- [ ] Run one approved, reversible end-to-end action in the test workspace.
- [ ] Preserve provider response evidence and distinguish an attempted action from a confirmed
      provider-side result.

## Demo and CV

- [ ] Record a 60–90 second flow: trigger, approval pause, approval, completion, audit trace and
      analytics.
- [ ] Use the synthetic qualifier beside every evaluation result.
- [ ] Put the project on the CV with the measured local claims; do not claim deployment, OAuth or
      customer outcomes until the corresponding evidence exists.

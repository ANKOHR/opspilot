# Verification and evidence boundary

This page is the reproducibility record for OpsPilot. It deliberately separates observed local and
deployed evidence from capabilities that are only staged for later configuration.

Last local verification: 2026-09-20.

## Verified locally

| Area | Command or observation | Evidence |
| --- | --- | --- |
| Backend quality | `\.venv\Scripts\python.exe -m ruff check apps packages` and `ruff format --check` | Clean lint and formatting checks |
| Backend behaviour | `\.venv\Scripts\python.exe -m pytest -q` | 60 passed; two dependency deprecation warnings; no test failures |
| Synthetic evaluation | `\.venv\Scripts\python.exe packages\evals\run_evals.py` | 100 generated cases: 100% intent, fit-band, approval-policy and schema-compliance metrics |
| Frontend quality | `pnpm lint`, `pnpm typecheck`, `pnpm build` | Production Next.js build completes |
| API flow | `POST /api/events` then approval decision | Run pauses, approval resumes it, and the final send result is explicitly `sent_in_sandbox` |
| Idempotency | Replay the same event key | The existing run is returned with `idempotent_replay: true` |
| RBAC | Viewer attempts a write route | API returns HTTP 403; read routes remain available |
| Traceability | Open a completed run | Ordered trace includes model/tool events, latency, cost, approval and completion records |
| Gmail boundary | `apps/api/tests/test_gmail.py` | OAuth state, encrypted refresh-token handling, MIME normalization and approval-gated fake Gmail execution pass without provider calls |

## Verified on Railway

| Area | Observation | Evidence |
| --- | --- | --- |
| Public repository | `ANKOHR/opspilot` is public on GitHub | [github.com/ANKOHR/opspilot](https://github.com/ANKOHR/opspilot) |
| Railway API | Production deployment `SUCCESS` at commit `d749bfe6e93da0ac04eef28dd0a7f91206bfdd47` | `https://api-production-35aff.up.railway.app/health` returned `{"status":"ok","service":"opspilot-api","mode":"production"}` |
| Database migration | Remote migration used Alembic `PostgresqlImpl` | Revision `0001_initial` observed inside the deployed API container |
| Railway services | API and worker deployments `SUCCESS`; Postgres and Redis `SUCCESS` | Railway project `opspilot`; API and worker commit `d749bfe6e93da0ac04eef28dd0a7f91206bfdd47` |
| Worker footprint | Dramatiq boot log showed two worker processes and a Prometheus fork process | Worker Dockerfile defaults to 2 processes and 4 threads for the trial instance |
| Vercel frontend | Production deployment `READY` from the monorepo `apps/web` root | [opspilot-web-iota.vercel.app](https://opspilot-web-iota.vercel.app/) returned HTTP 200 and rendered the dashboard |
| Frontend/API boundary | Production Vercel origin allowed by the Railway API | `OPTIONS /health` with `Origin: https://opspilot-web-iota.vercel.app` returned HTTP 200 and the matching `access-control-allow-origin` header |
| Gmail OAuth | Production callback completed for an authorized test account | `/api/integrations/gmail` returned `status: connected` with `gmail.readonly`, `gmail.compose` and `gmail.send` scopes; refresh credentials remain server-side |
| Gmail ingestion | Targeted production sync queued a Dramatiq job for the verification subject | One durable `gmail.email_received` run reached `waiting_for_approval`; the run created a live Gmail draft and recorded `external: true`, `provider: gmail` |
| Approval-gated Gmail send | Approval was performed from the public OpsPilot approval inbox | The run reached `succeeded`; the provider result returned `status: sent`, `external: true`, `sandbox: false` and `confirmed: true` with a Gmail message identifier; recipient delivery is not claimed |
| Production idempotency | Replayed the live Gmail event key against `POST /api/events` | The API returned the existing completed run rather than creating or sending a duplicate action |
| Production checkpoint replay | Replayed the completed run through `POST /api/runs/{run_id}/replay` | A new run recorded `replay_of`, paused at approval, and was rejected before `gmail.send`; no second outbound message was sent |
| Production RBAC | Viewer attempted `POST /api/demo/inbound-lead` | Railway API returned HTTP 403 with `Viewer role is read-only` |

## Not claimed

- No OpenAI or Anthropic request is made by the default demo. `DemoLLMProvider` is deterministic;
  the provider classes are explicit integration boundaries and currently require implementation
  and credentials before live calls.
- The local test suite uses a fake connector and does not create external Gmail side effects; the
  deployed verification above covers the separately authorized live Gmail test.
- HubSpot, Calendar and Slack remain represented by sandbox adapters. No external CRM record,
  calendar event or Slack post is sent.
- Docker Compose is defined but is not marked exercised until a Docker-capable host runs the stack.
- No recipient delivery, customer outcome, or production AI accuracy is claimed from the live Gmail
  self-test. The demo provider remains deterministic and explicitly labelled.
- Evaluation results are synthetic fixture metrics, not production accuracy or customer results.
- The current host has no `docker` executable, so the Compose stack has not been started here.

## Reproduce the local checks

From the repository root:

```powershell
.\scripts\verify.ps1
```

To include the optional Docker preflight when Docker is installed:

```powershell
.\scripts\verify.ps1 -IncludeDocker
```

The script does not silently turn an unavailable Docker installation into a pass. It reports the
stack as skipped and leaves the unverified state visible.

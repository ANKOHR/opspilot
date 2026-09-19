# Verification and evidence boundary

This page is the reproducibility record for OpsPilot. It deliberately separates observed local and
deployed evidence from capabilities that are only staged for later configuration.

Last local verification: 2026-09-20.

## Verified locally

| Area | Command or observation | Evidence |
| --- | --- | --- |
| Backend quality | `\.venv\Scripts\python.exe -m ruff check apps packages` and `ruff format --check` | Clean lint and formatting checks |
| Backend behaviour | `\.venv\Scripts\python.exe -m pytest -q` | 56 passed; two dependency deprecation warnings; no test failures |
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
| Railway API | Production deployment `SUCCESS` at commit `1a6b9bfe21b56a11f79d5d179f58860645309c60` | `https://api-production-35aff.up.railway.app/health` returned `{"status":"ok","service":"opspilot-api","mode":"production"}` |
| Database migration | Remote migration used Alembic `PostgresqlImpl` | Revision `0001_initial` observed inside the deployed API container |
| Railway services | API and worker deployments `SUCCESS`; Postgres and Redis `SUCCESS` | Railway project `opspilot`; worker commit `73fb12df021a200d877f74c68e6e22d9d160b472` |
| Worker footprint | Dramatiq boot log showed two worker processes and a Prometheus fork process | Worker Dockerfile defaults to 2 processes and 4 threads for the trial instance |
| Vercel frontend | Production deployment `READY` from the monorepo `apps/web` root | [opspilot-web-iota.vercel.app](https://opspilot-web-iota.vercel.app/) returned HTTP 200 and rendered the dashboard |
| Frontend/API boundary | Production Vercel origin allowed by the Railway API | `OPTIONS /health` with `Origin: https://opspilot-web-iota.vercel.app` returned HTTP 200 and the matching `access-control-allow-origin` header |

## Not claimed

- No OpenAI or Anthropic request is made by the default demo. `DemoLLMProvider` is deterministic;
  the provider classes are explicit integration boundaries and currently require implementation
  and credentials before live calls.
- Gmail has a real OAuth/API adapter in the repository, but this local verification did not connect
  a Google account or send a provider message. The default test suite uses a fake connector and no
  external Gmail side effect.
- HubSpot, Calendar and Slack remain represented by sandbox adapters. No external CRM record,
  calendar event or Slack post is sent.
- Docker Compose is defined but is not marked exercised until a Docker-capable host runs the stack.
- Gmail OAuth is not configured in the deployed environment yet. No Google account connection,
  provider message, recipient delivery, or customer outcome is claimed.
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

# Verification and evidence boundary

This page is the reproducibility record for the local OpsPilot build. It deliberately separates
observed local evidence from capabilities that are only staged for later configuration.

Last local verification: 2026-09-19.

## Verified locally

| Area | Command or observation | Evidence |
| --- | --- | --- |
| Backend quality | `\.venv\Scripts\python.exe -m ruff check apps packages` and `ruff format --check` | Clean lint and formatting checks |
| Backend behaviour | `\.venv\Scripts\python.exe -m pytest -q` | 48 passed; two dependency deprecation warnings; no test failures |
| Synthetic evaluation | `\.venv\Scripts\python.exe packages\evals\run_evals.py` | 100 generated cases: 100% intent, fit-band, approval-policy and schema-compliance metrics |
| Frontend quality | `pnpm lint`, `pnpm typecheck`, `pnpm build` | Production Next.js build completes |
| API flow | `POST /api/events` then approval decision | Run pauses, approval resumes it, and the final send result is explicitly `sent_in_sandbox` |
| Idempotency | Replay the same event key | The existing run is returned with `idempotent_replay: true` |
| RBAC | Viewer attempts a write route | API returns HTTP 403; read routes remain available |
| Traceability | Open a completed run | Ordered trace includes model/tool events, latency, cost, approval and completion records |

## Not claimed

- No OpenAI or Anthropic request is made by the default demo. `DemoLLMProvider` is deterministic;
  the provider classes are explicit integration boundaries and currently require implementation
  and credentials before live calls.
- Gmail, HubSpot, Calendar and Slack are represented by sandbox adapters. No OAuth token is stored
  and no external message, CRM record, calendar event or Slack post is sent.
- Docker Compose is defined but is not marked exercised until a Docker-capable host runs the stack.
- No public repository, hosted demo, public URL or customer outcome is claimed from this local
  workspace.
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

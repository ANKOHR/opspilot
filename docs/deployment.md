# Deployment runbook

The intended public topology is one Vercel project rooted at `apps/web` and one Railway project
named `opspilot` containing `api`, `worker`, Postgres and Redis services. The repository remains a
single monorepo; Railway service settings select the service-specific Dockerfile paths.

## Railway service configuration

After linking the Railway project and creating the four services, configure the two code services
with the repository root as their build context:

```powershell
railway environment edit --service-config api source.rootDirectory /
railway environment edit --service-config api build.dockerfilePath apps/api/Dockerfile
railway environment edit --service-config api deploy.healthcheckPath /health
railway environment edit --service-config worker source.rootDirectory /
railway environment edit --service-config worker build.dockerfilePath apps/worker/Dockerfile
```

The API and worker share `DATABASE_URL`, `REDIS_URL`, `APP_ENV`, `APP_SECRET`,
`CREDENTIAL_ENCRYPTION_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`,
`GOOGLE_OAUTH_REDIRECT_URI`, `GMAIL_SCOPES` and `WEB_APP_URL`. Postgres and Redis connection
variables should use Railway service references rather than copied credentials.

Run the versioned schema inside the deployed API container before the first API deployment is
considered healthy (the SSH key is registered with Railway for the workspace):

```powershell
railway ssh --service api --identity-file $env:USERPROFILE\.ssh\opspilot_railway -- python -m opspilot_api.migrate
```

Generate the public API domain, verify `/health`, then add that URL to Vercel as
`NEXT_PUBLIC_API_URL`. Set the Gmail OAuth callback to:

```text
https://<api-domain>/api/integrations/gmail/oauth/callback
```

## Vercel

Link the repository as a monorepo project with root directory `apps/web`. The install command is
`pnpm install --frozen-lockfile`; the build command is `pnpm --filter opspilot-web build`. Set
`NEXT_PUBLIC_API_URL` to the deployed Railway API origin and add that origin to
`API_CORS_ORIGINS` on Railway.

## Evidence requirements

Record the deployed commit, API `/health` response, migration revision, worker deployment status,
Postgres/Redis service status, Vercel URL and Gmail OAuth account in `docs/evidence.md`. A Gmail
API success response is provider acceptance of the request; verify the resulting message in Sent
Mail before describing the external action as confirmed.

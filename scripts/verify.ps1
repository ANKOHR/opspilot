[CmdletBinding()]
param(
    [switch]$IncludeDocker
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Expected project Python at $pythonPath"
}

Push-Location $projectRoot
try {
    Write-Host "[1/8] Ruff lint"
    & $pythonPath -m ruff check apps packages
    if ($LASTEXITCODE -ne 0) { throw "Ruff lint failed" }

    Write-Host "[2/8] Ruff format check"
    & $pythonPath -m ruff format --check apps packages
    if ($LASTEXITCODE -ne 0) { throw "Ruff format check failed" }

    Write-Host "[3/8] Backend tests"
    & $pythonPath -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed" }

    Write-Host "[4/8] Synthetic evaluations"
    & $pythonPath packages\evals\run_evals.py
    if ($LASTEXITCODE -ne 0) { throw "Synthetic evaluations failed" }

    Write-Host "[5/8] Frontend lint"
    & pnpm lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed" }

    Write-Host "[6/8] Frontend typecheck"
    & pnpm typecheck
    if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed" }

    Write-Host "[7/8] Production frontend build"
    & pnpm build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }

    if ($IncludeDocker) {
        Write-Host "[8/8] Docker Compose configuration"
        $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
        if ($null -eq $dockerCommand) {
            Write-Warning "Docker is not installed; Docker Compose was not exercised."
        } else {
            & docker compose config
            if ($LASTEXITCODE -ne 0) { throw "Docker Compose config failed" }
        }
    } else {
        Write-Host "[8/8] Docker Compose skipped (pass -IncludeDocker to preflight it)"
    }

    Write-Host "Verification completed. See docs/evidence.md for the claim boundary."
} finally {
    Pop-Location
}

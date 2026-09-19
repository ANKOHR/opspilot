# Evaluation protocol

`packages/evals/run_evals.py` generates 100 synthetic lead cases with expected intent, fit band
and approval policy labels. The runner reports accuracy and schema compliance as local fixture
metrics. It does not represent customer, production or deployment performance.

Run:

```powershell
.venv\Scripts\python.exe packages\evals\run_evals.py
```

The generated `eval-results.json` should be reviewed alongside the fixture generator. When a real
provider is connected, add human-reviewed cases and regression thresholds before using the results
in a public case study.


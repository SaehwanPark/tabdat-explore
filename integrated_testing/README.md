# Integrated Public-Dataset E2E Testing

This directory contains the reusable integrated testing harness for
`docs/e2e_public_dataset_test_plan.md`.

## What It Runs

- `s1_titanic_batch_core`: batch `-c` core EDA flow on Titanic.
- `s2_interactive_shell_contract`: prompt-toolkit completion and history checks through a TTY.
- `s3_taxi_lazy_scale`: lazy Parquet workflow on NYC taxi data, including SQL, plots, and save.
- `s4_penguins_script_repro`: script/config/nested-run/multiline-SQL workflow on Penguins.

The harness downloads public datasets into `artifacts/e2e/data/` and writes scenario outputs under
`artifacts/e2e/`. These generated files are intentionally ignored by git.

## Commands

Run all integrated scenarios:

```bash
uv run python integrated_testing/run_e2e.py
```

Run selected scenarios:

```bash
uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s4_penguins_script_repro
```

Keep generated artifacts from a previous run:

```bash
uv run python integrated_testing/run_e2e.py --no-clean
```

## Outputs

Each run creates:

- `integrated_testing/reports/latest/results.json`
- `integrated_testing/reports/latest/summary.md`
- per-scenario stdout/stderr logs

The report directory is ignored so large logs and transient local paths do not enter git. Copy only
curated observations into tracked docs when they matter for a PR.

## Validation

Before opening a PR, run:

```bash
uv run pytest
uv run mypy
uv run ruff check .
uv run ruff format --check .
uv run python integrated_testing/run_e2e.py
```

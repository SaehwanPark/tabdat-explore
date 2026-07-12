# Integrated Public-Dataset E2E Testing

This directory contains the reusable integrated testing harness for
`docs/e2e_public_dataset_test_plan.md`.

## What It Runs

- `s1_titanic_batch_core`: batch `-c` core EDA flow on Titanic.
- `s2_interactive_shell_contract`: prompt-toolkit completion and history checks through a TTY.
- `s3_taxi_lazy_scale`: lazy Parquet workflow on NYC taxi data, including SQL, plots, and save.
- `s4_penguins_script_repro`: script/config/nested-run/multiline-SQL workflow on Penguins.
- `s5_titanic_phase13_dogfood`: real-dataset `regress`/`predict`/`estat` flow on Titanic.
- `s6_canonical_parquet_workflow`: the published lazy Parquet EDA journey, replayed twice with
  output-equivalence and wall-clock timing checks.

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
- per-command wall-clock durations in `results.json`; the canonical scenario also records first
  run, replay, total, and output-shape metrics.

The report directory is ignored so large logs and transient local paths do not enter git. Copy only
curated observations into tracked docs when they matter for a PR.

## Validation

Before opening a PR, run:

```bash
uv run pytest
uv run basedpyright
uv run ruff check .
uv run ruff format --check .
uv run python integrated_testing/run_e2e.py
```

The P0 canonical workflow can be run on its own:

```bash
uv run python integrated_testing/run_e2e.py s6_canonical_parquet_workflow
```

It uses the Titanic public sample converted to Parquet, runs the tracked
`demos/canonical_parquet_eda.td` script twice, and records timings as observational benchmark
evidence. Timing values are not a host-independent pass/fail threshold.

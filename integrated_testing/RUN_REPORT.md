# Integrated E2E Run Report

Status: pass.

The integrated public-dataset harness lives in `integrated_testing/run_e2e.py`.

## Validation Commands

Executed successfully:

```bash
uv run pytest
uv run mypy
uv run ruff check .
uv run ruff format --check .
uv run python integrated_testing/run_e2e.py
```

## Observations

- `s1_titanic_batch_core` passed against `artifacts/e2e/data/titanic.parquet`.
- `s2_interactive_shell_contract` passed with isolated history under `artifacts/e2e/home`.
- `s3_taxi_lazy_scale` passed against the NYC taxi January 2023 Parquet dataset, including SVG
  plot checks and Parquet persistence.
- `s4_penguins_script_repro` passed with explicit config, nested `run`, multiline SQL, PNG plot
  output, and Parquet export.
- `s5_titanic_phase13_dogfood` passed with real-dataset `regress`, `predict`, and
  `estat residuals|ovtest|vif` coverage.

## Fixes

- Fixed a harness setup defect where DuckDB path parameters in a single CSV-to-Parquet `COPY`
  statement were bound in the wrong order.
- Corrected the E2E test plan expectations to match current product contracts: tabulate output
  uses `Row %` / `Col %`, and prompt-toolkit may show completion candidates without rewriting the
  buffer when a prefix is ambiguous.
- Corrected the script reproducibility scenario expectation to match `export` output wording
  (`Exported:` rather than `Saved:`).
- Added a dedicated Phase 13 real-dataset dogfood scenario so integrated coverage exercises
  `regress`, `predict`, and `estat` together.
- Fixed interactive shell Ctrl-C handling so completion interrupts return to the prompt instead of
  exiting with a traceback.

## Residual Risks

- The public dataset URLs are external dependencies; future failures should distinguish network
  or source availability from TabDat behavior.
- The TTY harness validates observable prompt-toolkit output, but terminal CPR warnings are ignored
  because they are environment-dependent and not product pass/fail signals.

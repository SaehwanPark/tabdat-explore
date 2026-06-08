# Phase 19 Slice 8 Implementation Report

## Scope

Implemented partial-linear DML on branch `temp/phase19-slice8-dml-linear-treatment`.

## What Changed

- Added `dml linear` parser command, `DmlCommand`/`DmlRegressionResult` models, and `estat dml`
  routing.
- Added cross-fitted sklearn Lasso nuisance estimation with statsmodels OLS final stage in executor.
- Added deterministic formatter output, shell completions, help topic, and extension-registry metadata.
- Added focused parser, executor, CLI, shell, help, and registry tests.
- Updated SDD docs and version to `0.17.0`.

## Validation Commands

- `uv run pytest tests/test_parser.py -q -k dml`
- `uv run pytest tests/test_executor.py -q -k dml`
- `uv run pytest tests/test_cli.py -q -k dml`
- `uv run basedpyright`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest`

Result: `834 passed`

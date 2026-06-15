# Spatial Residual Diagnostics Implementation Report

## Contract Consumed

`_workspace/01_product_command-contract.md`

## What Changed

- **Models**: Added `spatial` subcommand, weights path, ID variable, contiguity mode, coordinates, and KNN count to `EstatCommand` in `src/tabdat/models.py`.
- **Parser**: Added grammar parsing and constraint verification in `_parse_estat` in `src/tabdat/parser.py` (e.g. mutual exclusivity of weights/coordinates, rejecting options for other `estat` subcommands).
- **Executor**: Implemented `_execute_estat_spatial` in `src/tabdat/executor.py`. It aligns weight matrices, checks OLS sample size equality, reconstructs OLS models via `spreg.BaseOLS`, computes Moran's I (`MoranRes`) and LM tests (`LMtests` for simple and robust error/lag and SARMA), and outputs a formatted `TableResult`.
- **Shell UX**: Expanded autocompletions in `src/tabdat/shell.py` to support `estat spatial` and its options.
- **Help**: Documented the new subcommand in `src/tabdat/help/topics/estat.md`.
- **Durable docs**: Updated `SPEC.md`, `ARCHITECTURE.md`, and `CHANGELOG.md` to record the completed spatial diagnostics work.

## Validation Commands

- `uv run pytest tests/test_spregress.py -k spatial`
- `uv run pytest tests/test_parser.py -k spatial`
- `uv run basedpyright`
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run pytest` (917 passed)

## Known Gaps

- Out-of-sample spatial predictive workflows are deferred.
- Joint LM tests (like LM for WX, SDM joint tests) are deferred.

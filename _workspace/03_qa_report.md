# Spatial Residual Diagnostics (`estat spatial`) QA Report

## Status

pass

## Boundaries Checked

- **Contract to parser**: Validated that `estat spatial` option syntax, mutual exclusivity (e.g., `coord` vs `weights`), and subcommand-specific options are verified by the parser and throw `ParseError` when violated. Other `estat` subcommands correctly reject these options.
- **Parser representation to executor**: Verified that parsed `EstatCommand` fields (`coord_variables`, `knn`, `weights_file`, `id_variable`, `contiguity`) are correctly passed to and consumed by the execution path.
- **Executor to backend**: Verified that row extraction for coordinates or IDs filters out incomplete observations and ensures that the final estimation sample size matches the prior OLS regression's `nobs`.
- **Backend result to formatter & CLI**: Verified that OLS residuals are calculated on the reconstructed `BaseOLS` model, and spatial autocorrelation diagnostics (Moran's I, LM tests) are formatted into a clean `TableResult` conforming to the output design.
- **CLI/help/docs to contract**: Verified that help documentation `estat.md` and shell autocomplete completions correctly support the new subcommand and its options.

## Blocking Issues

- None.

## PR Review Loop

- PR: (Local repository feature branch `feat/estat-spatial`)
- Pass 1 verified option constraints and mutual exclusivity in parser logic.
- Pass 2 verified OLS estimation sample alignment constraints and PySAL weights handling.
- Pass 3 verified autocomplete integration in `src/tabdat/shell.py`.

## Non-Blocking Follow-Ups

- None.

## Validation Evidence

- Target parser tests passed: `uv run pytest tests/test_parser.py -k spatial`
- Target executor tests passed: `uv run pytest tests/test_spregress.py -k spatial`
- Full suite validation passed: `uv run pytest` (917 passed)
- Static validation passed: `uv run basedpyright` (0 errors, 0 warnings)
- Lint validation passed: `uv run ruff check` and `uv run ruff format --check`

## Recommended Next Action

- Merge branch `feat/estat-spatial` and proceed with PR handoff.

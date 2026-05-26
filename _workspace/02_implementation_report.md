# ROP Dependency and Parser Refactor Implementation Report

## Scope

Implemented the planned ROP maintenance slice on branch `temp/rop-comp-builders-pypi-parser`.

## What Changed

### Dependency checkpoint

- Replaced the Git direct reference for `comp-builders` with `comp-builders>=1.0.0` from PyPI.
- Regenerated `uv.lock` so `comp-builders==1.0.0` resolves from the PyPI registry.
- Removed the now-unneeded Hatch `allow-direct-references` setting.

### Monad boundary

- Kept `src/tabdat/monads.py` as the only runtime `comp_builders` import boundary.
- Re-exported `AsyncResult` and `async_result` through the local boundary.
- Added focused async-result tests through `tabdat.monads`.

### Parser ROP flow

- Added `_parse_command_result(...) -> Result[Command, str]`.
- Kept public `parse_command(...) -> Command` as the sole conversion point from `Result` to
  user-facing `ParseError`.
- Routed top-level `help`, `use`, `by`, `sql`, `run`, and structured-command parsing through
  result-returning helpers.
- Converted `by` child parsing to use the internal result path instead of recursively calling the
  public exception-raising parser path.
- Preserved existing command syntax and parse error text.

### SDD/docs

- Updated `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and workspace handoff artifacts.
- Recorded remaining Phase 19 slices in `SPEC.md`: machine-learning integration, Bayesian
  workflows, and spatial-model workflows.

## Validation Commands

Focused validation already run during implementation:

- `uv run python -c "import importlib.metadata as md; print(md.version('comp-builders'))"`
- `uv run pytest tests/test_monads.py -q`
- `uv run pytest tests/test_parser.py -q`
- `uv run pytest tests/test_monads.py tests/test_parser.py -q`
- `uv run pyright src/tabdat/parser.py src/tabdat/monads.py tests/test_monads.py tests/test_parser.py`
- `uv run mypy src/tabdat`

Final full validation is recorded in the delivery summary.

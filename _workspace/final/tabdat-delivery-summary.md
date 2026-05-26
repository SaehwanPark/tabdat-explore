# ROP Dependency and Parser Refactor Delivery Summary

## Outcome

Completed the bounded ROP maintenance slice and prepared the branch for review.

## Implemented

- Migrated `comp-builders` from the Git direct reference to PyPI `comp-builders>=1.0.0`.
- Removed obsolete direct-reference packaging metadata.
- Re-exported `AsyncResult` and `async_result` through `tabdat.monads`.
- Centralized parser `Result` flow behind public `parse_command`, preserving `ParseError`
  behavior.
- Converted `by` child parsing to use the internal result-returning parser path.
- Updated focused tests, SDD docs, and workspace handoff artifacts.

## Validation

- `uv run python -c "import importlib.metadata as md; print(md.version('comp-builders'))"`
- `uv run pytest tests/test_monads.py tests/test_parser.py -q`
- `uv run pyright src/tabdat/parser.py src/tabdat/monads.py tests/test_monads.py tests/test_parser.py`
- `uv run mypy src/tabdat`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest`

## Residual Risk

- This PR intentionally avoids executor/backend ROP refactors.
- Parser public behavior is expected to be unchanged; review should focus on preserving exact
  error behavior across CLI, shell, and script callers.

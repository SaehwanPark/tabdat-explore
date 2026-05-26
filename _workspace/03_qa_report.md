# ROP Dependency and Parser Refactor QA Report

## Status

pass

## Boundaries Checked

- Dependency -> runtime:
  - `comp-builders` resolves from PyPI as version `1.0.0`.
  - `pyproject.toml` and `uv.lock` no longer reference the GitHub dependency source.
- Runtime boundary:
  - `src/tabdat/monads.py` remains the only direct runtime import from `comp_builders`.
  - `Result`, `Option`, `Validation`, and `AsyncResult` are exposed through `tabdat.monads`.
- Parser boundary:
  - Public `parse_command` still returns `Command` values or raises `ParseError`.
  - Parser internals now compose top-level parsing through `Result` before edge conversion.
  - `by` child parsing uses the result-returning parser path and preserves nested/help guards.
- Documentation:
  - SDD docs record the PyPI dependency source, async-result boundary, and Phase 19 remaining
    slices.

## Blocking Issues

- None found in focused validation.

## Validation Evidence

- Focused monad and parser tests passed.
- Pyright and mypy passed for touched parser/monad/test surfaces and full `src/tabdat` mypy scope.
- Full validation commands are recorded in `_workspace/final/tabdat-delivery-summary.md`.

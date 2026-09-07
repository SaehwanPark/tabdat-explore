# QA Report: `missing` null-missingness report

## Verdict

`pass` (local implementation checks and focused review complete)

## Evidence

- Focused parser, eager/lazy backend, executor atomic-error, CLI human/JSON, shell completion, MCP,
  and docs-alignment coverage passed.
- Full `uv run pytest -q` passed: 1,293 tests, with only existing statistical/backend dependency
  warnings.
- Ruff lint and formatting checks passed.
- `basedpyright src` reported 0 errors, 0 warnings, and 0 notes.
- Documentation and command-alignment verification passed.
- Empty datasets return zero missing percentage; unknown variables fail before scanning; DuckDB and
  Polars-lazy results preserve requested/schema order and lazy session metadata.

## Review loop

Three independent passes over the branch diff covered command/state behavior, backend null/count
semantics and lazy execution, and user-facing/machine-interface/docs alignment. No actionable
findings were identified. The Polars empty-dataset path was manually exercised after the focused
suite and returned a zero-row, zero-percent result without changing lazy mode.

## Harness note

`verify_code` also invokes the repository's configured `mypy .` stage. That stage remains red on
pre-existing unrelated source/import issues (including duplicate module discovery for
`scripts/check_docs_alignment.py`); the project CI type gate is `basedpyright`, which passes with
zero diagnostics above.

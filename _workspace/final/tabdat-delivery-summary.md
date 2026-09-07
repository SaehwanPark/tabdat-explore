# Delivery Summary: `assert` quality gate

## Slice

Added the read-only `assert <boolean-expression>` command for deterministic active-row quality checks. True predicates pass; false or missing predicates fail with checked/failed counts. Empty datasets pass. The command preserves the active relation and Polars-lazy execution and remains intentionally TabDat-native rather than Stata/SAS/SPSS-compatible syntax.

## Surfaces changed

- Typed command/result models, parser, DuckDB/Polars-lazy backend, executor, formatter, CLI metadata, and shell completion.
- Focused tests plus CLI/shell coverage.
- In-app help, command reference, user guide, language semantics, architecture/spec/changelog, and README.
- Request, contract, implementation, and QA artifacts under `_workspace/`.

## Verification

- `uv run pytest -q` — 1,310 passed.
- Ruff lint and formatting checks passed.
- `uv run basedpyright src tests/test_assert.py` — 0 diagnostics.
- `uv run python scripts/check_docs_alignment.py` — passed.
- `verify_code` build/test/lint passed; mypy remains red only for known pre-existing dependency stubs and duplicate script-module discovery.

## Delivery note

This is one bounded branch/PR slice. No follow-up feature was started.

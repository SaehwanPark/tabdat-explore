# Implementation Report: `assert` quality gate

## Contract consumed

- `_workspace/01_product_command-contract.md`

## Delivered

- Added typed `AssertCommand`/`AssertResult` models and strict `assert <boolean-expression>` parsing.
- Reused TabDat expression inference and compilation so true predicates pass while false or SQL-NULL predicates fail; options, `if`, and assignment forms are rejected.
- Added DuckDB and Polars-lazy aggregate scans with deterministic checked/failed counts. Polars-lazy plans remain active and the command does not mutate dataset/session state.
- Added executor failure handling, human/JSON formatting, read-only CLI effect and command schema metadata, shell completion, help, command references, language semantics, user-guide, architecture, README, `SPEC.md`, and changelog updates.
- Added focused parser, backend/executor, empty-dataset, eager/lazy-engine, state-preservation, CLI text/JSON/error, and active-dataset tests.

## Validation

- `uv run pytest -q` — 1,310 passed, 320 existing dependency warnings.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed (61 files already formatted).
- `uv run basedpyright src tests/test_assert.py` — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed (links, command reference, and help-topic alignment).
- `verify_code` — pytest, build, and Ruff stages passed; configured mypy stage remains red on pre-existing untyped imports (`arviz`, `bambi`, `libpysal`) and duplicate module discovery for `scripts/check_docs_alignment.py`.

## Known limits

`assert` intentionally has no options, `if`, `by`, assignment, row filtering, custom missing-value rules, or row-level diagnostics. Descending/expression sorting and richer workflows remain outside this slice.

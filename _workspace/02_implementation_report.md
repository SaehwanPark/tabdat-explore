# Implementation Report: stable `sort` row ordering

## Contract

`_workspace/01_product_command-contract.md`

## Delivered

- Added `sort <varlist>` parsing, typed command support, executor dispatch, CLI schema/effect
  metadata, and shell command/column completion.
- Added stable ascending native-key ordering with nulls last and preserved tie order for DuckDB and
  Polars-lazy execution. Polars updates its lazy plan without eager conversion.
- Preserved all columns, variable/value labels, panel metadata, and existing transform result/JSON
  semantics.
- Updated in-app help, command reference/navigation, language/user-guide docs, README,
  architecture/spec/changelog records, and focused parser/backend/executor/CLI/shell tests.

## Validation

- `uv run pytest tests/test_sort.py tests/test_shell.py tests/test_cli.py tests/test_docs_alignment.py` — 209 passed.
- `uv run pytest -q` — 1,300 passed (320 warnings from existing statistical/backend dependencies).
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright src` — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed.

## Notes

Descending and expression-based sorting remain intentionally available through SQL rather than adding
another command option surface.

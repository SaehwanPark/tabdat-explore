# Implementation Report: label dictionary persistence

## Contract

`_workspace/01_product_command-contract.md`

## Delivered

- Added `label save <path> [, replace]` and `label use <path>` parsing, command models, execution, CLI schemas, and declared effects.
- Added deterministic schema-versioned UTF-8 JSON serialization in `src/tabdat/labels.py` with strict metadata validation and atomic replacement writes.
- Validated loaded variable references and value-label attachments before replacing active metadata; malformed or incompatible dictionaries leave session state unchanged.
- Preserved DuckDB/Polars lazy execution mode without materializing data for metadata save/use.
- Updated in-app help, command reference/navigation, language/persistence docs, README, architecture/spec/changelog records, and focused parser/serialization/executor/CLI tests.

## Validation

- `uv run pytest tests/test_labels.py tests/test_label_dictionary.py tests/test_cli.py` — 195 passed (including the full selected CLI module).
- `uv run pytest -q` — 1,284 passed (320 warnings from existing statistical/backend dependencies).
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright src` — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed.

## Notes

The dictionary format is intentionally TabDat-native and does not claim direct Stata, SAS, or SPSS metadata-file compatibility.

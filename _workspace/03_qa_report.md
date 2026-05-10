# Phase 9-10 Future Items QA Report

## Status

pass

## Boundaries Checked

- Contract to parser for unchanged `export <path>[, replace]` grammar across `.parquet`, `.csv`,
  and `.feather` suffixes.
- Executor to backend for distinct `save` versus `export` behavior and result formatting.
- Backend Polars lazy state to executor fallback behavior for supported lazy commands versus
  explicit eager materialization.
- CLI output to command contract for `Exported:` messaging and lazy row-count honesty.
- Docs to implementation for completed Phase 9 export scope and bounded Phase 10 Polars scope.

## Blocking Issues

- None found in validation.

## Non-Blocking Follow-Ups

- Broader Polars-native execution remains future work.
- Remote Polars lazy loading remains out of scope.
- Additional export ergonomics such as delimiter/compression options remain out of scope.

## Validation Evidence

- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py` passed.
- `uv run pytest` passed with 319 tests.
- `uv run pyright` passed.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed.

## Recommended Next Action

Push the branch, open the PR from `codex/tmp-phase9-phase10-future-items`, and mark it ready for
review.

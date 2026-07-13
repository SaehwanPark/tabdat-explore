# Implementation Report: Phase 24 P0 Active Row Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — current active row sequence, preview limits, filter
  retention, row-preserving transformations, cross-engine parity, and explicit ordering non-goals.

## Delivered Boundary

- `src/tabdat/help/topics/head.md`, `tail.md`, `keep.md`, and `drop.md`
  - Documented current-order `head`/`tail` behavior, zero limits, and retained-row relative order.
- `tests/test_executor.py`
  - Added an unsorted Parquet fixture with a missing predicate value.
  - Verified head, tail, zero limits, keep, and drop behavior across eager, DuckDB-lazy, and
    Polars-lazy execution.
  - Verified that select, rename, generate, replace, and recode preserve the active sequence across
    all three execution configurations.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered script-mode head output order and the new help guarantees.
- `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record the active row-order contract and mark this slice complete while keeping relation
    combination, arbitrary SQL, and categorical ordering separate.

## Functional-First Notes

The existing backend operations already preserve the supported active relation sequence: DuckDB
previews and filters operate on the active relation sequence, and Polars uses sequence-preserving
lazy operations. This slice adds executable contract coverage and user guidance without introducing
row IDs, hidden ordering metadata, or a new sorting abstraction.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'active_row_order_is_consistent or row_preserving_transformations_retain_active_sequence' -q` — passed, 6 tests.
- `uv run pytest tests/test_cli.py -k 'script_preserves_active_row_order' -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -q` — passed, 8 tests.
- `uv run pytest` — passed, 1,069 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

Append/join/reshape order, named-table storage order, arbitrary SQL ordering, categorical ordering,
exact arithmetic storage widths, overflow diagnostics, randomness, estimation samples, machine
output, exit semantics, and full operation lineage remain separate Phase 24 slices.

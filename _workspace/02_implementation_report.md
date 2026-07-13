# Implementation Report: Phase 24 P0 Grouped-Result Ordering

## Contract Consumed

- `_workspace/01_product_command-contract.md` — native numeric/text/boolean ordering, missing-last
  grouped keys, wide tabulate consistency, bar tie ordering, and explicit row-order non-goals.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Added a pure tagged ordering key for wide tabulate headers: numeric values sort numerically,
    booleans false before true, text lexicographically, and null/NaN last.
  - Kept row-key order from the already ordered DuckDB grouped result and applied the same key to
    wide column headers.
  - Changed bar tie-breaking to order by the native category value rather than its rendered string,
    while keeping descending counts and nulls last.
- `tests/test_executor.py`
  - Added eager, DuckDB-lazy, and Polars-lazy grouped fixtures covering numeric `2` versus `10`,
    text `a` versus `z`, missing keys, wide tabulates, long tabulates, and `by count`.
  - Added direct bar-count coverage for native tie ordering.
- `tests/test_cli.py`, `tests/test_help.py`, and help topics
  - Covered the user-visible numeric tabulate header order and documented grouped/bar ordering.
- `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record this bounded ordering contract and defer active row order, arbitrary SQL ordering, and
    categorical ordering to later slices.

## Functional-First Notes

The ordering policy is a pure key transformation over grouped result tuples. SQL remains responsible
for grouped aggregation and native row-key ordering; the formatter-side wide assembly consumes that
structured stream and applies one explicit deterministic key without mutating active dataset state.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'tabulate_one_way_and_two_way or grouped_results_use_native or bar_tie_order' -q` — passed, 5 tests.
- `uv run pytest tests/test_cli.py -k 'full_phase_3_eda_flow or native_numeric_tabulate' -q` — passed, 2 tests.
- `uv run pytest tests/test_help.py -k 'missing_values' -q` — passed, 1 test.
- `uv run pytest` — passed, 1,058 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

Active row-order guarantees, `head`/`tail` ordering, arbitrary SQL ordering, categorical ordering,
exact arithmetic storage widths, overflow diagnostics, randomness, estimation samples, machine
output, exit semantics, and full operation lineage remain separate Phase 24 slices.

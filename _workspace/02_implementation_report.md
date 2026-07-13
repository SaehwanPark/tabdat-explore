# Implementation Report: Phase 24 P0 SQL and Named-Table Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — explicit SQL result order, `sql ... into`, named-table
  reactivation, preview behavior, and unordered SQL/relation-combination non-goals.

## Delivered Boundary

- `tests/test_executor.py`
  - Verified direct `order by` SQL result rows across eager, DuckDB-lazy, and Polars-lazy inputs.
  - Verified `sql ... into` preserves query order through head/tail and after `use` reactivation.
  - Asserted the existing eager/fallback materialization state at the SQL boundary.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered script-mode ordered SQL through named-table activation and documented the explicit-order
    requirement.
- `src/tabdat/help/topics/sql.md`, `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`, and
  `_workspace/`
  - Record the SQL/named-table sequence contract and mark unordered SQL, relation combinations, and
    categorical order as separate work.

## Functional-First Notes

The existing SQL boundary already materializes `sql ... into` results into DuckDB tables, and the
active row-order contract now makes their stored sequence observable. This slice adds focused tests
and user guidance without rewriting SQL, adding row IDs, or introducing a second ordering layer.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'ordered_sql_results_survive_into_and_named_table_activation' -q` — passed, 3 tests.
- `uv run pytest tests/test_cli.py -k 'ordered_sql_through_named_table' -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -q` — passed, 8 tests.
- `uv run pytest` — passed, 1,074 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

SQL without explicit ordering, append/join/reshape order, categorical ordering, exact arithmetic
storage widths, overflow diagnostics, randomness, estimation samples, machine output, exit
semantics, and full operation lineage remain separate Phase 24 slices.

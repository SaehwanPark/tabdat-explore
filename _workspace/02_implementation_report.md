# Implementation Report: Phase 24 P0 SQL and Named-Table Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — explicit SQL result order, tie-breakers,
  `sql ... into`, named-table reactivation, activation-boundary state, and unordered SQL/
  relation-combination non-goals.

## Delivered Boundary

- `tests/test_executor.py`
  - Verified direct `order by` SQL result rows across eager, DuckDB-lazy, and Polars-lazy inputs.
  - Added a tied-key query with a secondary key and verified its reproducible total order.
  - Verified `sql ... into` preserves query order through head/tail and after isolated `use` reactivation.
  - Asserted the existing activation-boundary materialization state, including Polars fallback reset.
- `tests/test_parser.py`, `tests/test_cli.py`, and `tests/test_help.py`
  - Covered multiline ordered SQL with `into`, script-mode ordered SQL through reactivation, exact
    formatted preview rows, and SQL/use help guidance.
- `src/tabdat/help/topics/sql.md`, `src/tabdat/help/topics/use.md`, `docs/language-semantics.md`,
  `docs/user-guide.md`, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record explicit SQL order, tie-breaker requirements, named-table restoration, and the existing
    materialization reset semantics while keeping unordered SQL and relation combinations separate.

## Functional-First Notes

The existing SQL boundary already materializes `sql ... into` results into DuckDB tables, and the
active row-order contract makes their stored sequence observable. This slice adds focused tests and
user guidance without rewriting SQL, adding row IDs, or introducing a second ordering layer.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'ordered_sql_results_survive_into_and_named_table_activation' -q` — passed, 3 tests.
- `uv run pytest tests/test_cli.py -k 'ordered_sql_through_named_table' -q` — passed, 1 test.
- `uv run pytest tests/test_parser.py -k 'parse_phase_4_sql_commands' -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -q` — passed, 8 tests.
- `uv run pytest` — passed, 1,074 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

SQL without explicit ordering, tied SQL keys without a unique tie-breaker, append/join/reshape order,
categorical ordering, exact arithmetic storage widths, overflow diagnostics, randomness, estimation
samples, machine output, exit semantics, and full operation lineage remain separate Phase 24 slices.

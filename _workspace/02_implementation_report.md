# Implementation Report: Phase 24 P0 Categorical Ordering

## Contract Consumed

- `_workspace/01_product_command-contract.md` — native scalar label order, tabulate missing policy,
  bar count/tie order, collision-safe rendering, and no category metadata or level-management syntax.

## Delivered Boundary

- `tests/test_executor.py`
  - Verified numeric, text, boolean, and missing category order for tabulate and bar across eager,
    DuckDB-lazy, and Polars-lazy execution through fresh `BarCommand` artifacts.
  - Covered missing/reserved-label collisions in bar rendering and wide multi-key tabulate headers.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered missing category inclusion in CLI output and documented native/missing label behavior.
- `docs/language-semantics.md`, `src/tabdat/help/topics/tabulate.md`,
  `src/tabdat/help/topics/bar.md`, `docs/command-reference.md`, `SPEC.md`, `CHANGELOG.md`, and
  `_workspace/`
  - Record the categorical contract without adding a category data model or syntax.

## Functional-First Notes

The existing backend already sorts tabulate dimensions natively and bar counts by descending count
with native tie order. This slice makes that behavior a durable cross-engine contract and regression
boundary; rendered labels remain presentation values rather than sort keys.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'categorical_order_is_native_and_missing_last or bar_visualization or wide_tabulate_disambiguates' -q` — passed, 6 tests.
- `uv run pytest tests/test_cli.py -k preserves_native_numeric_tabulate_order -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k help_topics_document_explicit_missing_values -q` — passed, 1 test.
- `uv run pytest` — passed, 1,106 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green with matching replay stdout.

## Known Limits And Follow-Up Work

Unordered SQL, exact arithmetic storage widths, overflow diagnostics, randomness, estimation samples,
errors and exits, machine output, and full operation lineage remain separate Phase 24 slices. The three
required review passes are complete; merge and branch cleanup remain for this slice.

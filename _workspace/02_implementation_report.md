# Implementation Report: Phase 24 P0 Reshape Row Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — source-row/j-value order for long output,
  first-appearance identifier-group order for wide output, and append/join/categorical non-goals.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Added collision-safe source-row and j-value ordinals for `reshape long`, reserving all public
    output names.
  - Added a collision-safe first-source-row group ordinal for `reshape wide`, reserving generated
    output names.
  - Preserved existing generated-column order and duplicate-cell aggregation.
- `src/tabdat/executor.py`
  - Prevalidates long/wide identifiers, stubs, j-values, and output conflicts before Polars fallback
    so validation failures preserve active execution state.
- `tests/test_executor.py`
  - Verified eager, DuckDB-lazy, and Polars-lazy long/wide results using non-sorted source rows,
    non-lexicographic wide-column order, collision-prone names, null/duplicate cells, and failed
    validation state.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered exact CLI long output and documented source/group sequence behavior.
- `src/tabdat/help/topics/reshape.md`, `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`,
  and `_workspace/`
  - Record reshape sequence and validation semantics while keeping append, join, and categorical
    ordering separate.

## Functional-First Notes

Reshape now materializes explicit implementation-only sequence boundaries rather than relying on
identifier sorting or backend grouping order. Validation remains pure and precedes Polars fallback;
no row IDs, sort syntax, or duplicate-cell aggregation policy changes were introduced.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'reshape_preserves_source_and_group_sequence or reshape_internal_order_names_do_not_overwrite_public_columns or reshape_wide_preserves_null_and_duplicate_cell_behavior or failed_reshape_validation_preserves_active_state' -q` — passed, 10 tests.
- `uv run pytest tests/test_executor.py tests/test_cli.py -k reshape -q` — passed, 15 tests.
- `uv run pytest tests/test_cli.py -k phase_11_reshape_long_flow -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k help_topics_document_explicit_missing_values -q` — passed, 1 test.
- `uv run pytest` — passed, 1,101 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

Categorical ordering, unordered SQL, exact arithmetic storage widths, overflow diagnostics, randomness,
estimation samples, errors and exits, machine output, and full operation lineage remain separate Phase
24 slices.

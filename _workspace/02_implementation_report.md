# Implementation Report: Phase 24 P0 Reshape Row Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — source-row/j-value order for long output,
  first-appearance identifier-group order for wide output, and append/join/categorical non-goals.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Added collision-safe source-row and j-value ordinals for `reshape long`.
  - Added a collision-safe first-source-row group ordinal for `reshape wide`.
  - Preserved existing generated-column order and duplicate-cell aggregation.
- `tests/test_executor.py`
  - Verified eager, DuckDB-lazy, and Polars-lazy long/wide results using non-sorted source rows and
    non-lexicographic wide-column order.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered exact CLI long output and documented source/group sequence behavior.
- `src/tabdat/help/topics/reshape.md`, `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`,
  and `_workspace/`
  - Record reshape sequence semantics while keeping append, join, and categorical ordering separate.

## Functional-First Notes

Reshape now materializes explicit implementation-only sequence boundaries rather than relying on
identifier sorting or backend grouping order. No row IDs, sort syntax, or duplicate-cell aggregation
policy changes were introduced.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k reshape_preserves_source_and_group_sequence -q` — passed, 3 tests.
- `uv run pytest tests/test_executor.py tests/test_cli.py -k reshape -q` — passed, 8 tests.
- `uv run pytest tests/test_cli.py -k phase_11_reshape_long_flow -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k help_topics_document_explicit_missing_values -q` — passed, 1 test.
- `uv run pytest` — passed, 1,094 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

Categorical ordering, unordered SQL, exact arithmetic storage widths, overflow diagnostics, randomness,
estimation samples, errors and exits, machine output, and full operation lineage remain separate Phase
24 slices. PR review is the remaining handoff step for this slice.

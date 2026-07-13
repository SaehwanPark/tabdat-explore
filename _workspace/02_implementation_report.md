# Implementation Report: Phase 24 P0 Append Row Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — active-left then named-table-right sequence, no
  sorting/deduplication/interleaving, preview behavior, failure atomicity, and join/reshape non-goals.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Added explicit per-input ordinals and side ordering to append output, preventing `UNION ALL`
    planning from interleaving active and named-table rows.
  - Made head, tail, and DuckDB row filters explicitly order their current sequence snapshots.
  - Normalized Polars/DuckDB scalar type aliases for pre-materialization append validation.
- `src/tabdat/executor.py`
  - Validates named-table existence and append schema compatibility before Polars lazy fallback, so
    failed append commands preserve the active state.
- `tests/test_executor.py`
  - Verified eager, DuckDB-lazy, and Polars-lazy append order, duplicate-row preservation, head/tail,
    and failure atomicity for unknown tables, missing columns, and type mismatches.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered exact script-mode append row blocks and documented left-then-right behavior.
- `src/tabdat/help/topics/append.md`, `docs/language-semantics.md`, `docs/command-reference.md`,
  `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record append sequence semantics while keeping join, reshape, and categorical ordering separate.

## Functional-First Notes

Append now snapshots each input's current sequence into an internal side/ordinal ordering boundary,
then materializes the combined rows. Validation remains pure and precedes Polars fallback; no row IDs,
deduplication, or public sorting abstraction is introduced.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'append_preserves_left_then_right_sequence or failed_append_validation_preserves_active_state' -q` — passed, 6 tests.
- `uv run pytest tests/test_cli.py -k 'script_preserves_append_sequence' -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -q` — passed, 8 tests.
- `uv run pytest` — passed, 1,081 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

Join/reshape ordering, unordered SQL, categorical ordering, exact arithmetic storage widths, overflow
diagnostics, randomness, estimation samples, machine output, exit semantics, and full operation
lineage remain separate Phase 24 slices.

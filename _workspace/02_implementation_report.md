# Implementation Report: Phase 24 P0 Join Row Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — active-row grouping, named-table match order,
  duplicate preservation, inner/left unmatched behavior, and reshape/categorical non-goals.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Added a right-input ordinal to the existing active-input ordinal and ordered join output by
    active sequence first, then named-table sequence.
- `tests/test_executor.py`
  - Verified eager, DuckDB-lazy, and Polars-lazy inner/left joins with duplicate right matches and
    unmatched active rows.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered exact CLI join row blocks and documented active-row/match ordering.
- `src/tabdat/help/topics/join.md`, `docs/language-semantics.md`, `docs/command-reference.md`,
  `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record join sequence semantics while keeping append, reshape, and categorical ordering separate.

## Functional-First Notes

Join now snapshots both inputs into internal ordinal ordering boundaries before materialization. The
ordinals are implementation-only; no row IDs, deduplication, global sort, or public sorting abstraction
is introduced.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k join_preserves_active_and_match_sequence -q` — passed, 6 tests.
- `uv run pytest tests/test_cli.py -k phase_11_join_named_table_flow -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k help_topics_document_explicit_missing_values -q` — passed, 1 test.
- `uv run pytest` — passed, 1,087 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all integrated scenarios,
  including canonical replay, remained green.

## Known Limits And Follow-Up Work

Reshape ordering, unordered SQL, categorical ordering, exact arithmetic storage widths, overflow
diagnostics, randomness, estimation samples, errors and exits, machine output, and full operation
lineage remain separate Phase 24 slices. PR review is the remaining handoff step for this slice.

# Implementation Report: Phase 24 P0 Append Row Order

## Contract Consumed

- `_workspace/01_product_command-contract.md` — active-left then named-table-right sequence, no
  sorting/deduplication/interleaving, preview behavior, and join/reshape non-goals.

## Delivered Boundary

- `tests/test_executor.py`
  - Added eager, DuckDB-lazy, and Polars-lazy append fixtures with explicit named-table order.
  - Verified active rows precede appended rows, head/tail consume the combined sequence, and current
    materialization state reporting remains correct.
- `tests/test_cli.py` and `tests/test_help.py`
  - Covered script-mode append previews and documented left-then-right behavior.
- `src/tabdat/help/topics/append.md`, `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`, and
  `_workspace/`
  - Record append sequence semantics while keeping join, reshape, and categorical ordering separate.

## Functional-First Notes

The existing `append` backend query already uses `UNION ALL` over the active relation followed by the
named table. This slice locks that sequence as a user-facing contract without adding row IDs, sorting,
deduplication, or a relation-combination abstraction.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'append_preserves_left_then_right_sequence' -q` — passed, 3 tests.
- `uv run pytest tests/test_cli.py -k 'script_preserves_append_sequence' -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -q` — passed, 8 tests.
- `uv run pytest` — passed, 1,078 tests, with 314 existing third-party warnings.
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

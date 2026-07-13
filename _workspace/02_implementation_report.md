# Implementation Report: Phase 24 P0 Missing Predicate Semantics

## Contract Consumed

- `_workspace/01_product_command-contract.md` — missing values, row predicates, and aggregate
  policy.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Makes `keep if` treat missing predicates as false.
  - Makes `drop if` remove only true predicates and retain false/missing predicate rows in DuckDB
    and Polars execution.
- `tests/test_executor.py`
  - Covers keep/drop/replace missing-condition behavior across eager, DuckDB-lazy, and Polars-lazy
    sessions.
  - Covers `summarize`, `codebook`, `tabulate ..., missing`, and the rendered `bar ..., missing`
    behavior on existing null data, including all-missing numeric input.
- `tests/test_cli.py`
  - Covers the user-facing `drop if` result in both `-c` and script execution.
- `docs/language-semantics.md`, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record the stable missingness policy and bounded follow-up scope.

## Implementation Notes By Boundary

- SQL uses `(not (condition)) or (condition) is null` for `drop if`.
- Polars fills a missing keep predicate with false and a missing drop predicate with true before
  filtering.
- Existing replace-if behavior already preserves values when the condition is false or missing and
  is now covered as part of the cross-engine contract.
- Aggregate/profiling behavior remains backend-native and is documented with focused evidence rather
  than introducing a new missing-value type or syntax.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'missing_predicates_are_consistent or tabulate_missing_option_controls or all_missing_numeric or phase_24_bar_missing' -q` — passed, 6 tests.
- `uv run pytest tests/test_cli.py -k 'missing_drop_predicate' -q` — passed, 2 tests.
- `uv run pytest` — passed, 984 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed; all six integrated scenarios completed,
  including exact canonical replay.

## Known Limits And Follow-Up Work

- Explicit missing predicates/null literals, coercion, arithmetic, categorical behavior, ordering,
  randomness, estimation samples, machine output, exit semantics, and full operation lineage remain
  separate Phase 24 slices.
- Missing values continue to use the existing SQL NULL/Python None representation.

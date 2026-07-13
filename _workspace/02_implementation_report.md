# Implementation Report: Phase 24 P0 Stable Arithmetic Overflow Diagnostics

## Contract Consumed

- `_workspace/01_product_command-contract.md` — informational `overflow rows: N` diagnostics for
  exact integral arithmetic in `generate`, `replace`, `keep`, and `drop`, with unchanged values and
  missingness.

## Delivered Boundary

- `src/tabdat/models.py` and `src/tabdat/formatter.py`
  - Added typed `overflow_count` to `TransformResult` with a zero-compatible default.
  - Appended `overflow rows: N` only for positive counts, preserving all existing zero-count output.
- `src/tabdat/backend.py`
  - Added a typed overflow probe that identifies exact integral arithmetic subexpressions, excludes
    bare identifiers, and counts only nonmissing rows before mutation.
  - Applied optional replacement-condition scoping and preserved existing invalid/nonfinite/division
    policies.
- `src/tabdat/executor.py`
  - Counts diagnostics before successful `generate`, `replace`, `keep`, and `drop` commits.
  - Keeps validation and fallback atomicity intact across eager, DuckDB-lazy, and Polars-lazy paths.
- Help/docs/tests
  - Documented the terminal diagnostic and its exclusions in language semantics, command reference,
    and generate/replace/keep/drop help.
  - Added positive overflow, zero-count, missing/false predicate, division, decimal-scale, floating,
    CLI, help, and cross-engine coverage.

## Functional-First Notes

The overflow probe is a pure AST/schema classification followed by one read-only backend count before
the impure relation mutation. The typed transform result carries the diagnostic explicitly instead of
encoding it in an unstructured side channel.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'integral_arithmetic_preserves_exact_decimal_width_and_overflow_policy or integral_replace_preserves_exact_width or integral_arithmetic_predicate_uses_exact_missing_policy' -q` — passed, 12 tests.
- `uv run pytest tests/test_executor.py -k 'numeric_expression_compatibility or arithmetic_results_normalize or replace_normalizes_row_level_arithmetic_results or arithmetic_predicates_treat_nonfinite_results_as_missing or decimal_arithmetic_predicates_use_numeric_missing_policy' -q` — passed, 21 tests.
- `uv run pytest tests/test_cli.py -k exact_integer_arithmetic -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k 'help_topics_document_explicit_missing_values or help_topics_document_expression_domains' -q` — passed, 2 tests.
- `uv run pytest` — passed, 1,122 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all scenarios passed and
  canonical replay stdout matched.

## Known Limits And Follow-Up Work

Machine-readable diagnostics, SQL-result metadata, decimal-scale/floating diagnostics, arbitrary
precision, operation lineage, randomness, estimation samples, and exit-code redesign remain separate
Phase 24 contracts. PR review is the remaining handoff step for this slice.

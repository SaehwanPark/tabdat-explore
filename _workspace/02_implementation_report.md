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
  - Added a typed overflow probe that recursively identifies maximal exact integral arithmetic
    subexpressions, excludes bare identifiers, and counts only nonmissing probe operands.
  - Applied replacement-expression scoping, independent predicate probes, and null-aware conditions
    without changing existing invalid/nonfinite/division policies.
  - Added a rollback token for Polars fallback materialization so diagnostic-count failures restore
    the lazy frame and session metadata.
- `src/tabdat/executor.py`
  - Validates `generate` targets before counting and counts diagnostics before successful `generate`,
    `replace`, `keep`, and `drop` commits.
  - Keeps validation and fallback atomicity intact across eager, DuckDB-lazy, and Polars-lazy paths.
- Help/docs/tests
  - Documented the terminal diagnostic and its exclusions in language semantics, command reference,
    and generate/replace/keep/drop help.
  - Added positive overflow, zero-count, missing/false predicate, division, decimal-scale, floating,
    nested, conditional-replace, injected-failure, CLI, help, and cross-engine coverage.

## Functional-First Notes

The overflow probe is a pure AST/schema classification followed by one read-only backend count before
the impure relation mutation. The typed transform result carries the diagnostic explicitly instead of
encoding it in an unstructured side channel.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'integral_arithmetic_preserves_exact_decimal_width_and_overflow_policy or integral_replace_preserves_exact_width or integral_arithmetic_predicate_uses_exact_missing_policy' -q` — passed, 12 tests.
- Overflow review regressions — passed, 34 focused tests across nested expressions, conditional
  replacement, Polars rollback, nonfinite/floating values, and decimal keep/drop behavior.
- `uv run pytest tests/test_cli.py -k exact_integer_arithmetic -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k 'help_topics_document_explicit_missing_values or help_topics_document_expression_domains' -q` — passed, 2 tests.
- `uv run pytest -q` — passed, 1,141 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood s6_canonical_parquet_workflow` — passed with exit code 0; all scenarios passed and canonical replay stdout matched.
- Exactly three independent PR reviews completed; all findings were fixed, and no fourth review was
  started.

## Known Limits And Follow-Up Work

Machine-readable diagnostics, SQL-result metadata, decimal-scale/floating diagnostics, arbitrary
precision, operation lineage, randomness, estimation samples, and exit-code redesign remain separate
Phase 24 contracts. The reviewed implementation is ready for PR update and merge.

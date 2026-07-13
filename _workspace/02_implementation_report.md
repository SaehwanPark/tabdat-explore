# Implementation Report: Phase 24 P0 Expression Coercion

## Contract Consumed

- `_workspace/01_product_command-contract.md` — expression domains, compatibility rules, predicate
  typing, replacement target-domain validation, and backend type normalization.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Added pure AST/domain inference for numeric, string, boolean, other, and null values.
  - Allowed numeric-family comparisons/arithmetic while rejecting mixed-domain comparisons,
    arithmetic, and typed function arguments with deterministic `TypeMismatchExecutionError`
    diagnostics.
  - Required boolean or missing row predicates and same-domain/null replacement expressions.
  - Preserved target types for direct null replacement by casting NULL to the declared target type.
  - Rejected unsafe unsigned-column/negative-literal combinations for eager/lazy parity.
  - Canonicalized Arrow/Polars numeric and categorical type names without classifying nested types by
    prefix.
  - Added non-materializing tabulate validation for dimensions, values/statistics, conditions, and
    duplicate `by:` dimensions.
- `src/tabdat/executor.py`
  - Routed all Polars-lazy tabulate and replacement validation through preflight checks before
    fallback materialization.
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`
  - Covered numeric compatibility, mixed-domain failures, predicate truthiness, target-domain and
    null replacement, unsigned parity, complete tabulate preflight, lazy-state preservation,
    CLI/script diagnostics, and help documentation.
- `docs/language-semantics.md`, help topics, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record the stable coercion contract and deferred categorical/arithmetic scope.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'numeric_expression_compatibility or mixed_domain or predicate_truthiness or tabulate_predicate_type' -q` — passed, 17 tests.
- `uv run pytest tests/test_executor.py -k 'null_replacement_preserves_target_domain or unsigned_numeric_negative or invalid_polars_tabulate_validation or failed_polars_tabulate_null_validation' -q` — passed, 8 tests.
- `uv run pytest tests/test_cli.py -k 'expression_type_mismatch' -q` — passed, 2 tests.
- `uv run pytest tests/test_help.py -k 'expression_domains' -q` — passed, 1 test.
- `uv run pytest` — passed, 1,025 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed; all six integrated scenarios completed,
  including exact canonical replay.

## Known Limits And Follow-Up Work

Categorical conversion beyond storage-domain normalization, string concatenation, ordering,
randomness, estimation samples, machine output, exit semantics, and full operation lineage remain
separate Phase 24 slices.

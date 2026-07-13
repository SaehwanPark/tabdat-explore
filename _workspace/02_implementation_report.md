# Implementation Report: Phase 24 P0 Exact Integer Arithmetic Result Widths

## Contract Consumed

- `_workspace/01_product_command-contract.md` — exact `DECIMAL(38,0)` integral results, row-level
  overflow missingness, existing division/non-finite behavior, and no new syntax.

## Delivered Boundary

- `src/tabdat/backend.py`
  - Classified integral arithmetic subtrees independently from floating and scale-bearing decimal
    expressions.
  - Cast integral `+`, `-`, `*`, and unary minus operands to `DECIMAL(38,0)` before evaluation so
    values do not inherit narrow backend integer widths.
  - Kept the existing `try`/finite normalization boundary so out-of-domain results become missing.
  - Exposed exact-arithmetic detection to route Polars-lazy predicates through the existing DuckDB
    fallback when exact evaluation is required.
- `src/tabdat/executor.py`
  - Preserved normal Polars-lazy filtering for ordinary predicates while materializing exact integer
    arithmetic predicates through the validated fallback path.
- `tests/test_executor.py`, `tests/test_cli.py`, and `tests/test_help.py`
  - Covered signed/unsigned boundary values, widened multiplication, unary minus, overflow, replace,
    row predicates, CLI output, and help text across eager/DuckDB-lazy/Polars-lazy paths.
- `docs/language-semantics.md`, help topics, command reference, `SPEC.md`, `CHANGELOG.md`, and
  `_workspace/`
  - Record exact integer width and row-level overflow semantics while deferring scale, float width,
    arbitrary precision, and stable overflow diagnostics.

## Functional-First Notes

The pure expression classifiers make the exact-width decision from the typed dataset schema and AST;
DuckDB remains the effectful materialization boundary. Polars-lazy predicates that need exact integer
arithmetic use the existing explicit fallback rather than silently accepting a backend-specific wrap.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'integral_arithmetic_preserves_exact_decimal_width_and_overflow_policy or integral_replace_preserves_exact_width or integral_arithmetic_predicate_uses_exact_missing_policy' -q` — passed, 9 tests.
- `uv run pytest tests/test_cli.py -k exact_integer_arithmetic -q` — passed, 1 test.
- `uv run pytest tests/test_help.py -k help_topics_document_expression_domains -q` — passed, 1 test.
- `uv run pytest tests/test_executor.py -k 'arithmetic or numeric_expression_compatibility' -q` — passed, 39 tests.
- `uv run pytest` — passed, 1,116 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed with exit code 0; all scenarios passed and
  canonical replay stdout matched.

## Known Limits And Follow-Up Work

Decimal-scale/precision propagation, floating result widths, arbitrary precision, stable overflow
error/warning diagnostics, randomness, estimation samples, machine output, and full operation lineage
remain separate Phase 24 contracts. PR review is the remaining handoff step for this slice.

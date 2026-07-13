# Implementation Report: Phase 24 P0 Explicit Missing Predicates

## Contract Consumed

- `_workspace/01_product_command-contract.md` — `null` literal, null-aware equality/inequality, and
  bounded invalid-null diagnostics.

## Delivered Boundary

- `src/tabdat/models.py`, `src/tabdat/parser.py`
  - Added a typed `NullExpression` AST node.
  - Parsed unquoted `null` case-insensitively while preserving quoted `` `null` `` identifiers.
- `src/tabdat/backend.py`
  - Compiled null-aware equality/inequality to SQL `is null`/`is not null` and equivalent Polars
    expressions in either operand order.
  - Supported direct all-missing generation/replacement.
  - Rejected null arithmetic and function arguments before state-changing execution.
  - Filled Polars predicate nulls before negation so direct `drop if null` remains cross-engine
    consistent.
- `src/tabdat/executor.py`
  - Validated direct and `by:` tabulate conditions before Polars-lazy fallback materialization,
    preserving lazy state on invalid null expressions.
- `tests/test_parser.py`, `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`
  - Covered parser, eager/DuckDB-lazy/Polars-lazy behavior, direct assignment, invalid operations,
    CLI/script execution, and discoverable help examples.
- `docs/language-semantics.md`, help topics, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record the stable explicit-missing contract and deferred coercion boundary.

## Validation Commands And Outcomes

- `uv run pytest tests/test_parser.py -k 'null_literal' -q` — passed, 1 test.
- `uv run pytest tests/test_executor.py -k 'explicit_null_predicates or null_literal_rejects' -q` —
  passed, 9 tests.
- `uv run pytest tests/test_cli.py -k 'explicit_missing_predicate' -q` — passed, 2 tests.
- `uv run pytest tests/test_help.py -k 'explicit_missing' -q` — passed, 1 test.
- `uv run pytest tests/test_executor.py -k 'failed_polars_tabulate_null_validation' -q` — passed, 2
  tests.
- `uv run pytest` — passed, 999 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed; all six integrated scenarios completed,
  including exact canonical replay.

## Known Limits And Follow-Up Work

Implicit numeric/string coercion, broader arithmetic-result policy, categories, ordering, randomness,
estimation samples, machine output, exit semantics, and full operation lineage remain separate Phase
24 slices.

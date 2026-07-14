# Request Summary: Phase 24 P0 Estimation Sample, Randomness, and Exit Semantics

## Goal
Implement stable cross-command semantics for:
1. `e(sample)` tracking and evaluation in expressions.
2. Seed propagation for reproducible randomness.
3. Clean CLI exit codes (0: success, 1: execution error, 2: syntax error, 3: file/system error).

## Phase Fit
Phase 24 P0: Product-Center Stabilization and Public Preview Gate.

## Touched Surfaces
- `src/tabdat/backend.py`: SUPPORTED_FUNCTIONS, active_dataset_info, _compile_expression_raw, _compile_polars_expression, add_boolean_column_from_values.
- `src/tabdat/executor.py`: regress, logit, other estimators, evaluating/saving estimation sample masks.
- `src/tabdat/cli.py`: _run_commands, _run_script, error catching, exit code mapping.
- `docs/language-semantics.md`: specifications update.
- `tests/test_executor.py`, `tests/test_cli.py`: test coverage.

## Assumptions
- `e(sample)` evaluates as an expression to a boolean (True/False).
- It is only valid with exactly one argument: the identifier `sample` (case-insensitive).
- System-internal columns starting with `__` are excluded from user-facing column metadata.
- Exits return 2 for syntax errors, 3 for missing files/configs, 1 for execution errors, 0 for success.

## Non-Goals
- Adding new econometric models/estimators.
- Exposing other estimation results like coefficients/covariance via expression evaluation (retained for future phases).
- Supporting `e(sample)` across sessions.

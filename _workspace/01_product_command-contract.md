# Product Contract: Phase 24 P0 — Estimation Sample, Randomness, and Exit Semantics

## Request Summary
Implement stable cross-command semantics for:
1. `e(sample)` tracking and evaluation in expressions.
2. Seed propagation for reproducible randomness.
3. Clean CLI exit codes (0: success, 1: execution error, 2: syntax error, 3: file/system error).

## Roadmap Phase
Phase 24 P0: Product-Center Stabilization and Public Preview Gate.

## Invocation & Semantics Rules

### 1. Estimation Sample `e(sample)`
- **Syntax**: `e(sample)` (case-insensitive function name and argument).
- **Semantics**: Evaluates to `True` for observations used in the last estimation, and `False` otherwise.
- **Hidden Column**: Tracking is backed by a hidden boolean column `__esample` in the active dataset. Hidden columns starting with `__` are excluded from all user-visible schema details (such as `describe` and `codebook`).
- **Compilation**:
  - DuckDB: Compiles to `__esample` (avoiding window function limitations).
  - Polars: Compiles to `pl.col("__esample")`.
- **Validation**:
  - `e(sample)` requires exactly one argument, which must be the identifier `sample`. Any other arguments (e.g. `e(age)` or `e(sample, 2)`) raise a `TypeMismatchExecutionError` or `ExecutionError`.
  - If no estimation model has been successfully fit in the session, or if the active dataset has changed since the fit, evaluating `e(sample)` raises an `ExecutionError` ("no active estimation sample available").

### 2. Randomness & Seeds
- Option `seed(value)` or script directive `seed value` configures the random number generator seed.
- Seed value must be a non-negative integer.
- Global seed is propagated to all estimators and functions using random number generation (e.g., bootstrap in `drdid`, folds in `dml`, MCMC in `bayes`, downsampling in `estat report`).

### 3. Exits & Errors
- CLI and script runners return:
  - `0` on successful completion.
  - `1` for execution-related errors (`ExecutionError` and its subclasses, database failures).
  - `2` for syntax and parser errors (`ParseError`).
  - `3` for system, environment, or file errors (missing script files, missing config files).

## Examples

Evaluating `e(sample)`:
```stata
regress wage educ exper
generate in_sample = e(sample)
keep if e(sample)
```

Invalid arguments:
```stata
generate bad = e(age)
# Error: e() requires exactly one argument 'sample'
```

No active estimation:
```stata
use data.parquet
keep if e(sample)
# Error: no active estimation sample available
```

Exit Codes:
```bash
# Syntax error
tabdat -c "generate bad ="
# Exit code: 2

# Missing file
tabdat missing_file.td
# Exit code: 3

# Execution error
tabdat -c "use missing.parquet"
# Exit code: 1
```

## Acceptance Criteria
- [ ] `e(sample)` compiles and evaluates correctly as a boolean column `__esample`.
- [ ] Internal columns starting with `__` are invisible in `describe` and `codebook`.
- [ ] Evaluated `e(sample)` raises correct errors when no estimation has run or arguments are invalid.
- [ ] Exit status codes return `0`, `1`, `2`, or `3` according to the failure type.
- [ ] Test suite and E2E integration scenarios pass completely.

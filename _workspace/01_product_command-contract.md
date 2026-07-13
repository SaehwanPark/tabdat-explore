# Product Contract: Phase 24 P0 — Stable Arithmetic Overflow Diagnostics

## Request Summary

Report deterministic row-level counts for exact integral arithmetic overflow without changing the
existing missing-result policy or adding syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This adds a small diagnostic layer on top of the completed exact integer-width contract. It does not
turn overflow into a command failure or redesign numeric storage.

## Existing Syntax

Valid forms retain the current grammar:

- `generate total = amount * factor`
- `replace amount = amount * factor if active == true`
- `keep if amount * factor > 0`
- `drop if amount * factor > 0`

No new operators, options, commands, or numeric literals are introduced. Successful transform
results expose an optional typed `TransformResult.overflow_count` diagnostic field, defaulting to
zero; the terminal formatter appends it only when positive.

## Diagnostic Rules

- Exact integral arithmetic continues to use `DECIMAL(38,0)` and turns out-of-domain results into
  missing values for affected rows.
- A successful `generate`, `replace`, `keep`, or `drop` result reports `overflow rows: N` when one or
  more rows overflowed an exact integral arithmetic expression. `N` counts only rows affected by the
  command's expression or predicate.
- A zero overflow count preserves the existing transform message and terminal shape; no noisy zero
  diagnostic is added.
- Missing operands are excluded from the overflow count. False or missing predicates, division by
  zero, invalid numeric-function domains, computed non-finite values, scale-bearing decimal arithmetic,
  and floating arithmetic are not classified as exact integer overflow.
- Overflow diagnostics are informational: the command still succeeds, retains valid rows/values, and
  applies existing missing/predicate policies.

## Data And Execution Assumptions

- The backend counts overflow using the typed expression and active relation before the successful
  row-preserving transformation commits. Failed validation leaves active data and status unchanged.
- Polars-lazy exact arithmetic predicates continue through the existing validated fallback; the
  diagnostic count and `polars_fallback` materialization reason remain consistent with eager/DuckDB.
- Diagnostics are currently terminal transform-result text only; stable JSON/JSONL envelopes and SQL
  result metadata remain separate automation contracts.

## Acceptance Criteria

- [ ] Generate and replace report positive exact-integer overflow counts while preserving missing rows.
- [ ] Keep and drop report predicate overflow counts with correct missing/false predicate behavior.
- [ ] Missing operands, non-finite/zero-division/decimal-scale/floating cases are not misclassified.
- [ ] Eager, DuckDB-lazy, and Polars-lazy output and fallback metadata agree.
- [ ] Zero-count output remains backward compatible; CLI/help/docs, focused tests, full validation, and
  integrated workflow checks pass.

## Non-Goals For This Slice

- Changing overflow missingness, arbitrary precision, decimal-scale/floating diagnostics, SQL-only
  diagnostics, machine-readable output, operation lineage, new syntax, estimators, or exit codes.

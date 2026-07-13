# Product Contract: Phase 24 P0 — Exact Integer Arithmetic Result Widths

## Request Summary

Make integral arithmetic in existing expressions exact within one explicit bounded result domain,
with deterministic row-level overflow behavior and no new syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This closes the exact-width boundary deferred by the earlier arithmetic-result slice. It does not
redesign decimal scales, floating widths, or user-facing overflow diagnostics.

## Existing Syntax

Valid forms retain the current grammar:

- `generate total = amount + 1`
- `replace amount = amount * 2 if active == true`
- `keep if amount - adjustment > 0`

No new operators, options, commands, result fields, or numeric literals are introduced.

## Exact Integer Rules

- Integral `+`, `-`, `*`, and unary minus expressions use `DECIMAL(38,0)` as their exact result
  domain. This includes signed and unsigned integer columns (including native `UHUGEINT` and
  Arrow/Polars `UINT128` aliases) and integer literals when every operand in the arithmetic subtree
  is integral.
- Representable results preserve their exact integer value and result width across eager, DuckDB-lazy,
  and Polars-lazy write paths. A normal terminal preview renders integral values without a fractional
  suffix even though the stored result is decimal-backed.
- A result outside `DECIMAL(38,0)` becomes missing for that row. There is no integer wraparound, and
  other rows in `generate`, `replace`, or a row predicate remain eligible under their existing
  missing/predicate policies.
- Real division remains real division. Floating operands, decimal-scale operands, numeric functions,
  zero-denominator behavior, invalid-domain behavior, and computed non-finite normalization retain
  their existing contracts.

## Data And Execution Assumptions

- Existing native column types and parser ASTs identify integral subtrees; no categorical or numeric
  metadata model is introduced.
- DuckDB is the materialization and exact-result boundary. Polars-lazy writes continue through the
  existing validated fallback path; Polars predicate compilation uses the same exact result domain
  when the result is representable.
- Overflow diagnostics as stable error/warning output, arbitrary precision, decimal-scale policy, and
  floating-width guarantees remain separate contracts.

## Acceptance Criteria

- [ ] Integral addition, subtraction, multiplication, and unary minus return exact decimal-backed
  values rather than backend-width wraparound or float coercion.
- [ ] Signed and unsigned boundary fixtures agree across eager, DuckDB-lazy, and Polars-lazy paths.
- [ ] Out-of-domain results become row-level missing without mutating unrelated rows.
- [ ] Existing real division, decimal-scale arithmetic, non-finite, and mixed-domain behavior remains
  green.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format checks, and integrated workflow
  checks pass.

## Non-Goals For This Slice

- New arithmetic syntax, arbitrary precision, stable overflow diagnostics, decimal-scale/precision
  redesign, float-width guarantees, randomness, estimators, lineage, machine output, or exit-code
  redesign.

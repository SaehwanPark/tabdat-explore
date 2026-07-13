# Product Contract: Phase 24 P0 — Explicit Missing Predicates

## Request Summary

Add a small, cross-engine expression contract for selecting and assigning missing values explicitly.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Explicit Null Syntax

- The unquoted token `null` is a case-insensitive missing-value literal. It produces SQL NULL/Python
  None semantics and is not a special numeric sentinel.
- `value == null` and `null == value` are true only when `value` is missing.
- `value != null` and `null != value` are true only when `value` is nonmissing.
- `null == null` is true and `null != null` is false.
- A direct `null` expression is permitted for all-missing generated/replaced values and as a row
  predicate; it follows the existing keep/drop missing-result policy.
- The quoted identifier `` `null` `` remains an ordinary, exact-spelling variable name.
- Null-aware equality/inequality are the only comparisons added in this slice. Null used with other
  operators, unary arithmetic, or functions fails with a stable execution diagnostic rather than
  relying on backend coercion.

## Existing Missingness Policy

- Missing values are null values (`None` at the Python boundary).
- `keep if` retains only true predicates; false and missing predicate results are excluded.
- `drop if` removes only true predicates; false and missing predicate results are retained.
- `replace if` updates only true predicates; false and missing conditions preserve the original value.
- `summarize` aggregates nonmissing numeric values; `codebook` reports nonmissing and missing counts.
- `tabulate` and `bar` omit missing categories by default and include them with `missing` where
  supported.

## Error Contract

Existing command-specific errors remain the public diagnostics; wording remains covered by focused
tests and may be refined only through a future language-error policy slice.

## Execution Semantics

- Predicate semantics apply consistently in eager and supported lazy paths.
- Null-aware comparisons compile to `is null`/`is not null` in SQL and equivalent Polars expressions.
- No implicit numeric/string coercion is introduced.

## Acceptance Criteria

- [x] Durable language-semantics documentation covers the `null` literal and null-aware comparisons.
- [x] Parser recognizes `null` while preserving quoted `` `null` `` identifiers.
- [x] Keep/drop/replace explicit missing predicates are tested across eager, DuckDB-lazy, and
  Polars-lazy paths.
- [x] Direct null assignment and invalid null arithmetic/function diagnostics are covered.
- [x] CLI and script paths, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- `is null`, `missing()`, and `nonmissing()` syntax; implicit numeric/string coercion; null arithmetic;
  categories; ordering; randomness; estimation samples; machine output; exit codes; or new commands.

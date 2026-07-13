# Product Contract: Phase 24 P0 — Arithmetic Results

## Request Summary

Make existing arithmetic and numeric-function syntax produce stable missing and finite results
across eager, DuckDB-lazy, and Polars-lazy execution.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded follow-up to the Phase 24 expression-coercion slice. It defines the result policy
for the existing expression grammar without adding syntax, commands, or new numeric types.

## Existing Syntax

Valid forms retain the current grammar:

- `generate ratio = numerator / denominator`
- `replace score = sqrt(raw_score) if eligible == "yes"`
- `keep if numerator / denominator > 0`

No new operators, functions, options, or output columns are introduced by this slice.

## Result Rules

- Arithmetic operators `+`, `-`, `*`, and `/`, plus unary minus, continue to require numeric
  operands under the expression-coercion contract.
- A missing operand produces a missing result for arithmetic and numeric functions. The explicit
  `null` literal remains rejected by arithmetic and functions; missing values from data columns are
  handled as results.
- Division is real division. A zero denominator produces a missing result for that row, including
  `0 / 0`; it does not expose infinity or NaN.
- `sqrt(x)` produces missing when `x < 0`; `ln(x)` and `log(x)` produce missing when `x <= 0`.
- Any computed NaN or infinity from supported arithmetic or numeric functions becomes missing.
- A direct identifier expression does not rewrite an existing source NaN or infinity. Normalization
  applies to values produced by arithmetic or numeric-function nodes.
- A valid finite result remains numeric. Exact backend-specific storage widening and overflow
  diagnostics are not promised by this slice.

## Expression Domains

- Numeric DuckDB types and numeric literals belong to one `numeric` domain. Numeric widening within
  that domain is allowed and remains backend-native.
- Unsafe unsigned-column and negative-literal combinations are rejected deterministically to preserve
  eager/lazy parity.
- `VARCHAR`/text values and string literals belong to the `string` domain.
- Polars categorical storage is canonicalized to the `string` domain; nested/list types are not
  classified as numeric by prefix matching.
- Boolean columns and comparison results belong to the `boolean` domain.
- Other backend scalar types remain an `other` domain and are not coerced into numeric or string.
- The existing `null` literal is a special missing domain. Null-aware `==`/`!=` behavior remains the
  explicit-missing contract.

## Compatibility Rules

- Equality/inequality and ordering comparisons require matching domains, except that any numeric
  pair is compatible and either side may be `null` under the existing null contract.
- Arithmetic and unary minus require numeric operands. String concatenation and implicit parsing are
  not introduced.
- Numeric expression functions (`abs`, `ceil`, `floor`, `ln`, `log`, `round`, `sqrt`) require one
  numeric argument. `lower` and `upper` require one string argument.
- Row conditions for `keep`, `drop`, `replace if`, and `tabulate if` must produce boolean or missing;
  numeric/string truthiness is rejected.
- `replace target = expression` permits a null expression or an expression in the target's domain;
  cross-domain replacement is rejected before the active relation changes.
- Mixed-domain failures use `TypeMismatchExecutionError` with deterministic expression diagnostics.

## Existing Missingness Policy

- Missing values are null values (`None` at the Python boundary).
- `keep if` retains only true predicates; false and missing predicate results are excluded.
- `drop if` removes only true predicates; false and missing predicate results are retained.
- `replace if` updates only true predicates; false and missing conditions preserve the original value.
- `summarize` aggregates nonmissing numeric values; `codebook` reports nonmissing and missing counts.
- `tabulate` and `bar` omit missing categories by default and include them with `missing` where
  supported.

## Error Contract

Mixed-domain failures use `TypeMismatchExecutionError` with stable expression diagnostics. Existing
command-specific error wording remains unchanged outside this slice. Row-level arithmetic domain
errors handled by this contract become missing values rather than command failures.

## Execution Semantics

- Predicate semantics apply consistently in eager and supported lazy paths.
- Null-aware comparisons compile to `is null`/`is not null` in SQL and equivalent Polars expressions.
- No implicit numeric/string coercion is introduced; existing validation occurs before Polars-lazy
  fallback materialization. Numeric result normalization is compiled in both DuckDB SQL and Polars
  expressions before the backend executes a supported operation.

## Acceptance Criteria

- [x] Durable language-semantics documentation covers arithmetic result and non-finite policy.
- [x] Missing operands, zero denominators, invalid numeric-function domains, and computed non-finite
  results agree across eager, DuckDB-lazy, and Polars-lazy paths.
- [x] Row-level arithmetic edge cases remain usable in `generate`, `replace`, and predicate flows.
- [x] Invalid expression validation remains atomic and occurs before Polars-lazy fallback.
- [x] CLI/script/docs, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- New expression syntax, categorical conversion, string concatenation, exact arithmetic storage-width
  guarantees, overflow reporting, ordering, randomness, estimation samples, machine output, exit
  codes, or new commands.

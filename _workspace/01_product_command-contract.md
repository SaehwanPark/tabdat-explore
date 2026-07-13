# Product Contract: Phase 24 P0 — Expression Coercion

## Request Summary

Make existing expression syntax obey stable scalar-domain compatibility across eager, DuckDB-lazy,
and Polars-lazy execution.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

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
command-specific error wording remains unchanged outside this slice.

## Execution Semantics

- Predicate semantics apply consistently in eager and supported lazy paths.
- Null-aware comparisons compile to `is null`/`is not null` in SQL and equivalent Polars expressions.
- No implicit numeric/string coercion is introduced; validation occurs before Polars-lazy fallback
  materialization, including tabulate dimensions, values/statistics, and `by:` duplicate checks.

## Acceptance Criteria

- [x] Durable language-semantics documentation covers expression domains and coercion boundaries.
- [x] Numeric-family expressions remain compatible across eager, DuckDB-lazy, and Polars-lazy paths.
- [x] Mixed-domain comparisons/arithmetic/functions fail deterministically before mutation.
- [x] Predicate and replacement target-domain validation is covered, including Polars-lazy state.
- [x] CLI/script/help/docs, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- New expression syntax, categorical conversion, string concatenation, ordering, randomness,
  estimation samples, machine output, exit codes, or new commands.

# Product Contract: Phase 24 P0 — Missing Predicate Semantics

## Request Summary

Document and regression-test how existing commands treat missing values in predicates and aggregates.

## Roadmap Phase

Phase 24 P0, workstream 2: stable language semantics before broader command and estimator expansion.

## Stable Missingness Policy

- Missing values are null values (`None` at the Python boundary), not a special numeric sentinel.
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
- No new missing predicate syntax or null literal is introduced.

## Acceptance Criteria

- [x] Durable language-semantics documentation covers predicate and aggregate missingness.
- [x] Keep/drop predicate behavior is tested across eager, DuckDB-lazy, and Polars-lazy paths.
- [x] Replace-if behavior for false and missing conditions is covered.
- [x] Summarize/codebook missing-count behavior is covered.
- [x] Full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- Explicit missing predicates/null literals, coercion, arithmetic, categories, ordering, randomness,
  estimation samples, machine output, exit codes, or new commands.

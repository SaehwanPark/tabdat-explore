# Product Contract: Phase 24 P0 — Identifier Spelling and Quoted Identifiers

## Request Summary

Document and regression-test exact variable spelling plus backtick-quoted identifiers in the command
language.

## Roadmap Phase

Phase 24 P0, workstream 2: stable language semantics before broader command and estimator expansion.

## Stable Identifier Policy

- Bare identifiers preserve exact spelling and are case-sensitive; command names remain
  case-insensitive.
- Bare identifiers use Unicode letters/underscore for the first character and Unicode letters, digits,
  or underscore thereafter.
- Backtick-quoted identifiers may contain whitespace and punctuation and use doubled backticks to
  represent one literal backtick.
- Quoted identifiers are accepted in variable targets, variable lists, and expression references;
  command names and option names remain unquoted keywords.
- Empty quoted identifiers are invalid, and exact spelling mismatches remain unknown-variable errors.

## Error Contract

Existing command-specific errors remain the public diagnostics. Exact spelling mismatches use the
existing unknown-variable diagnostics; wording remains covered by focused tests and may be refined
only through a future language-error policy slice.

## Execution Semantics

- Existing eager/lazy materialization and write-target atomicity behavior remain unchanged.
- Quoted identifiers resolve through the same backend identifier-quoting boundary as bare identifiers.

## Acceptance Criteria

- [x] Durable language-semantics documentation covers exact spelling and backtick quoting.
- [x] Parser accepts quoted identifiers in targets, lists, and expressions.
- [x] Quoted keywords remain identifiers rather than control keywords.
- [x] Backend execution preserves quoted names and exact case.
- [x] Full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- Missing values, coercion, arithmetic, categories, ordering, randomness, estimation samples,
  machine output, exit codes, SQL identifier syntax, or new commands.

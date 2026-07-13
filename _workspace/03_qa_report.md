# QA Report: Phase 24 P0 Arithmetic Results

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on missing propagation, finite numeric results, invalid numeric domains,
  and unsigned arithmetic rejection.
- **AST/backend compilation:** arithmetic and numeric functions normalize at expression boundaries;
  nested SQL expressions are bound once, and comparison operands receive safe numeric boundaries.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy paths agree for missing operands,
  zero denominators, invalid `sqrt`/`ln`/`log`, Decimal operand order, source NaN/infinity, and
  unsigned subtraction/unary minus rejection.
- **Failure behavior:** unsupported unsigned arithmetic is rejected before execution; row-level
  numeric domain failures become missing values; existing validation and active-dataset boundaries
  remain intact.
- **User-facing paths:** CLI `-c`, command help, canonical script replay, and language docs cover
  the result policy.
- **Scope control:** no new syntax, categorical conversion, string concatenation, command, or
  estimator was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Initial arithmetic executor regressions: 15 passed.
- Final review-fix executor regressions: 28 passed.
- Focused CLI regressions: 3 passed; help regressions: 2 passed.
- `uv run pytest` — 1,053 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** found Medium unsigned unary/subtraction parity and repeated SQL numeric subexpressions.
- **Pass 2:** found Medium Decimal division with a literal on the left and independently confirmed
  unsigned arithmetic divergence.
- **Pass 3:** independently confirmed the same unsigned parity and SQL duplication risks.

Fixed by rejecting unsigned subtraction/unary minus before backend execution, using a Float64-safe
Polars finite/result probe for Decimal expressions, and compiling raw nested SQL under one scalar
numeric-result projection. All three agents were closed after their reports; no fourth review pass
was created. No Critical or High findings remain.

## Non-Blocking Follow-Ups

Exact arithmetic storage widths and overflow diagnostics, categorical conversion, string
concatenation, ordering/randomness, estimation samples, machine output, exit semantics, lineage,
differential assurance, and public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the review-fix commit, update the PR body, mark the PR ready, merge it, then fast-forward
`main` and clean up the feature branch.

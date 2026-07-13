# QA Report: Phase 24 P0 Exact Integer Arithmetic Result Widths

Status: implementation validation complete; PR review pending

## Boundaries Checked

- **Contract to implementation:** `SPEC.md`, language semantics, generate/replace help, command
  reference, and the product contract agree on exact `DECIMAL(38,0)` integral results.
- **Exactness:** signed and unsigned integral addition, subtraction-compatible trees, multiplication,
  and unary minus preserve exact values beyond narrow BIGINT widths.
- **Overflow:** values beyond the bounded exact domain become row-level missing without wrapping or
  aborting unrelated rows.
- **Execution parity:** eager, DuckDB-lazy, and Polars-lazy generate/replace paths agree; exact
  arithmetic predicates use the validated Polars fallback and agree with DuckDB.
- **Scope control:** decimal-scale arithmetic, floating widths, arbitrary precision, stable overflow
  diagnostics, new syntax, estimator behavior, and lineage remain deferred.

## Blocking Issues

- None remain.

## Validation Evidence

- Exact-width, replace, and predicate regressions: 9 passed across three engines.
- CLI regression: 1 passed; focused help regression: 1 passed.
- Existing arithmetic compatibility regressions: 39 passed.
- `uv run pytest` — 1,116 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay with matching stdout.

## PR Review Loop

Exactly three independent review passes are required after the PR is opened. Reviewers must check
the arithmetic contract, backend width/overflow behavior, lazy fallback state, CLI/docs alignment,
and regression coverage. No fourth review pass is permitted.

## Non-Blocking Follow-Ups

Decimal-scale/precision propagation, floating result widths, arbitrary precision, stable overflow
diagnostics, unordered SQL, randomness, estimation samples, machine output, and full operation
lineage remain queued in `SPEC.md` Future.

## Recommended Next Action

Commit the validated exact-integer slice, push it, open the PR, and complete exactly three independent
review passes before any merge.

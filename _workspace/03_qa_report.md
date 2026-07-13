# QA Report: Phase 24 P0 Exact Integer Arithmetic Result Widths

Status: three-review pass complete; fixes validated; PR #103 ready for merge

## Boundaries Checked

- **Contract to implementation:** `SPEC.md`, language semantics, generate/replace help, command
  reference, and the product contract agree on exact `DECIMAL(38,0)` integral results.
- **Exactness:** signed and unsigned integral addition, subtraction-compatible trees, multiplication,
  and unary minus preserve exact values beyond narrow BIGINT widths.
- **Overflow:** values beyond the bounded exact domain become row-level missing without wrapping or
  aborting unrelated rows.
- **Execution parity:** eager, DuckDB-lazy, and Polars-lazy generate/replace paths agree; exact
  arithmetic predicates use the validated Polars fallback and agree with DuckDB.
- **Atomicity:** invalid exact predicates are rejected before Polars fallback, preserving lazy state,
  materialization metadata, and the last successful operation.
- **Type coverage:** native `UHUGEINT` and Arrow/Polars `UINT128` aliases are classified as unsigned
  integral types for the exact-width policy.
- **Scope control:** decimal-scale arithmetic, floating widths, arbitrary precision, stable overflow
  diagnostics, new syntax, estimator behavior, and lineage remain deferred.

## Blocking Issues

- None remain.

## Validation Evidence

- Exact-width, replace, and predicate regressions: 15 passed, including UHUGEINT and failed-state
  coverage.
- CLI regression: 1 passed; focused help regression: 1 passed.
- Existing arithmetic compatibility regressions: 46 passed.
- `uv run pytest` — 1,122 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay with matching stdout.

## PR Review Loop

Exactly three independent review passes completed on PR #103. Findings and fixes:

- Pass 1: added `UHUGEINT`/`UINT128` type coverage and a replace-overflow regression.
- Pass 2: validated complete `keep`/`drop` predicates before fallback and preserved failed lazy state.
- Pass 3: added successful keep/drop fallback metadata coverage and corrected the related handoff
  claims and stale PR state.

No fourth review pass is planned.

## Non-Blocking Follow-Ups

Decimal-scale/precision propagation, floating result widths, arbitrary precision, stable overflow
diagnostics, unordered SQL, randomness, estimation samples, machine output, and full operation
lineage remain queued in `SPEC.md` Future.

## Recommended Next Action

Commit and push the validated review fixes, update PR #103, wait for its required checks, merge it to
`main`, delete the local and remote feature branch, and return to the next `SPEC.md` item.

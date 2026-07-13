# QA Report: Phase 24 P0 Materialization-Reason Taxonomy

Status: implementation validation pass; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, command reference, user guide, and status help agree on
  the three public reason phrases and their scope.
- **Typed taxonomy:** `SessionState` and `StatusResult` accept only the two tracked reasons or
  `none`; formatter mapping is explicit and type-checked.
- **Transition detection:** successful DuckDB-lazy to eager commands report `eager operation`,
  while successful Polars fallback reports the more-specific `polars fallback`; the generic
  predicate explicitly excludes Polars lazy state.
- **Reset/failure boundary:** source/table activation resets the reason; failed commands do not
  commit a new reason; status/count preserve existing behavior.
- **Public surfaces:** `-c`, script, no-active, eager/lazy, named-table, help, and documentation
  flows are covered.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest` — 967 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six scenarios passed; canonical replay kept
  exact stdout/table equivalence with 4.324 seconds composite duration.

## PR Review Loop

- **Pass 1:** found no actionable issues across executor transitions, typed output, and failure/reset
  behavior.
- **Pass 2:** found no actionable issues across the reason taxonomy, precedence, formatter, and
  CLI/script paths.
- **Pass 3:** identified two Low findings: the generic predicate did not explicitly restrict itself
  to DuckDB lazy state, and user-guide reset wording omitted named-table/SQL activation. Fixed with
  the engine predicate, a Polars regression test, and corrected documentation.
- No Critical, High, or unresolved Medium findings remain.

## Non-Blocking Follow-Ups

- Backend-internal traces, operation lineage/history, retained estimation samples, and machine
  output remain intentionally queued in `SPEC.md`.

## Recommended Next Action

Commit the validated slice, open the PR, and run the three independent review passes.

# QA Report: Phase 24 P0 Materialization Reason Transparency

Status: implementation validation pass; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, the command reference, user guide, and status help topic
  agree on the new field, exact public phrase, reset behavior, and narrow Polars-fallback scope.
- **Contract to typed state:** `SessionState` and `StatusResult` carry an optional literal reason;
  the formatter maps the internal value to stable terminal text.
- **Fallback boundary:** successful Polars fallback records the reason after backend collection;
  the executor commits it only after the requested command returns successfully; failed fallback
  paths do not claim success.
- **Reset boundary:** successful source loads, named-table activation, and `sql ... into <table>`
  clear the prior reason.
- **Non-materialization boundary:** status remains before the materialization hook, and unsupported
  nested `by ...: status` fails before that hook without changing lazy state.
- **Public surfaces:** `-c`, script, parser, shell completion, help, exact no-active output, and
  docs are covered.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest` — 962 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six scenarios passed; canonical replay kept
  exact stdout/table equivalence with 4.362 seconds composite duration.

## PR Review Loop

- **Pass 1:** identified that fallback reason metadata was committed before a command could fail,
  and that `sql ... into` did not reset the reason. Fixed with a pending-metadata commit boundary,
  reset precedence, and regression tests for failed fallback and SQL activation.
- **Pass 2:** independently identified the same two Medium findings; both were fixed and rerun
  through focused, full-suite, type/lint, and integrated validation.
- **Pass 3:** found no actionable issues across typed state, fallback/reset behavior, CLI/script
  paths, and documentation.
- No Critical or High findings remained; both Medium findings were fixed rather than deferred.

## Non-Blocking Follow-Ups

- Broader materialization-cause taxonomy, operation lineage, active-operation progress, retained
  estimation samples, and machine-readable output remain intentionally queued in `SPEC.md`.

## Recommended Next Action

Commit the validated slice, open the PR, and run the three independent review passes.

# QA Report: Phase 24 P0 Materialization Reason Transparency

Status: implementation validation pass; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, the command reference, user guide, and status help topic
  agree on the new field, exact public phrase, reset behavior, and narrow Polars-fallback scope.
- **Contract to typed state:** `SessionState` and `StatusResult` carry an optional literal reason;
  the formatter maps the internal value to stable terminal text.
- **Fallback boundary:** successful Polars fallback records the reason after backend collection;
  failed fallback does not claim success.
- **Reset boundary:** successful source loads and named-table activation clear the prior reason.
- **Non-materialization boundary:** status remains before the materialization hook, and unsupported
  nested `by ...: status` fails before that hook without changing lazy state.
- **Public surfaces:** `-c`, script, parser, shell completion, help, exact no-active output, and
  docs are covered.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest` — 961 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six scenarios passed; canonical replay kept
  exact stdout/table equivalence with 4.363 seconds composite duration.

## PR Review Loop

- Three independent code-review passes will run after the PR is opened.
- Findings, fixes, and final disposition will be recorded here before merge.

## Non-Blocking Follow-Ups

- Broader materialization-cause taxonomy, operation lineage, active-operation progress, retained
  estimation samples, and machine-readable output remain intentionally queued in `SPEC.md`.

## Recommended Next Action

Commit the validated slice, open the PR, and run the three independent review passes.

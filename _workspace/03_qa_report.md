# QA Report: Phase 24 P0 Active Row Order

Status: local validation complete; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on current active row order, filter retention, and explicit non-goals.
- **Preview semantics:** unsorted head/tail fixtures, tail relative order, and zero limits agree
  across eager, DuckDB-lazy, and Polars-lazy execution.
- **Filter semantics:** keep/drop preserve surviving relative order, and missing predicate results
  follow the existing keep/drop policy in every supported execution path.
- **Transform semantics:** select, rename, generate, replace, and recode retain row sequence while
  changing columns or values.
- **User-facing paths:** script-mode CLI output and help text cover the contract.
- **Scope control:** no sort syntax, row IDs, hidden ordering metadata, relation-combination rewrite,
  arbitrary SQL rewrite, categorical ordering, or estimator behavior was added.

## Blocking Issues

- None found in local validation.

## Validation Evidence

- Cross-engine row-order executor regressions: 6 passed.
- Script-mode CLI regression: 1 passed; help suite: 8 passed.
- `uv run pytest` — 1,069 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Pending. The delivery protocol requires exactly three independent review passes after the PR is
opened; any actionable findings will be fixed and rechecked before merge.

## Recommended Next Action

Commit the validated slice, open the PR, and run the three independent review passes.

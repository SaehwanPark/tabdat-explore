# QA Report: Phase 24 P0 Active Row Order

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on current active row order, filter retention, explicit DuckDB insertion
  ordering, Polars fallback boundaries, and relation-changing non-goals.
- **Preview semantics:** explicitly ordered unsorted fixtures, head/tail relative order, and zero
  limits agree across eager, DuckDB-lazy, and Polars-lazy execution.
- **Filter semantics:** keep/drop preserve surviving relative order, and missing predicate results
  follow the existing keep/drop policy in every supported execution path.
- **Transform semantics:** select, keep/drop column projection, rename, generate, replace, and
  recode retain row sequence on fresh executors; lazy materialization state is asserted per command.
- **Polars fallback:** direct Polars-lazy recode validates before materialization and executes through
  the existing fallback path instead of failing without a DuckDB active relation.
- **User-facing paths:** script-mode CLI output covers head, tail, and row-filter order; help text
  and language docs cover the contract.
- **Scope control:** no sort syntax, row IDs, hidden ordering metadata, relation-combination rewrite,
  arbitrary SQL rewrite, categorical ordering, or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine row-order and isolated transformation/recode regressions: 8 passed.
- Script-mode CLI regressions: 2 passed; help suite: 8 passed.
- `uv run pytest` — 1,070 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** identified implicit DuckDB scan-order reliance, missing cross-engine projection
  coverage, and an unspecified collapse transition. Fixed by explicitly enabling insertion-order
  preservation, isolating projection cases, and documenting relation-changing result sequences.
- **Pass 2:** identified direct Polars-lazy recode failure, implicit DuckDB ordering, and masked
  transformation-engine coverage. Fixed by moving recode after the fallback boundary with
  pre-materialization validation, explicitly enforcing the DuckDB setting, and using fresh executors
  with per-command state assertions.
- **Pass 3:** identified the same ordering risk plus incidental fixture order and incomplete CLI
  coverage. Fixed with explicit fixture ordinals and ordering, and script-mode tail/filter tests.

No Critical or unresolved High/Medium findings remain.

## Non-Blocking Follow-Ups

Collapse and append/join/reshape ordering, named-table storage order, arbitrary SQL ordering,
categorical ordering, exact arithmetic widths, overflow diagnostics, randomness, estimation samples,
errors and exits, lineage, differential assurance, and public-preview readiness remain queued in
`SPEC.md`.

## Recommended Next Action

Push the review-fix commit, update PR #97, merge it, fast-forward `main`, and clean up the feature
branch.

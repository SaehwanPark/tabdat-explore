# QA Report: Phase 24 P0 Grouped-Result Ordering

Status: implementation validation complete; PR review pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on native grouped-key ordering and the row-order non-goals.
- **Pure result assembly:** wide tabulate headers use tagged numeric/text/boolean/null keys rather
  than rendered strings; row keys remain deterministic.
- **Backend ordering:** DuckDB grouped queries retain native `ORDER BY`; bar ties use the source
  category expression with explicit null-last ordering.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy tabulate fixtures agree for numeric,
  text, and missing keys.
- **User-facing paths:** CLI numeric header output, help text, canonical script replay, and language
  docs cover the contract.
- **Scope control:** no sort syntax, active row-order metadata, arbitrary SQL rewrite, categorical
  ordering, command, or estimator was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Focused ordering executor regressions: 5 passed.
- Focused ordering CLI regressions: 2 passed; help regression: 1 passed.
- `uv run pytest` — 1,058 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Pending: exactly three independent review passes will be completed on the pull request before merge.

## Non-Blocking Follow-Ups

Active row order, `head`/`tail`, arbitrary SQL ordering, categorical ordering, exact arithmetic
widths, overflow diagnostics, randomness, estimation samples, machine output, exit semantics,
lineage, differential assurance, and public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the reviewed commit, mark the PR ready, merge it, then fast-forward `main` and clean up the
feature branch.

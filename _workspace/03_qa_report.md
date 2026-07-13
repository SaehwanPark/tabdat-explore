# QA Report: Phase 24 P0 Grouped-Result Ordering

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on native grouped-key ordering and the row-order non-goals.
- **Pure result assembly:** wide tabulate headers use exact tagged numeric/text/boolean/null keys;
  canonical NaN keys prevent duplicate headers and split cell lookups.
- **Backend ordering:** DuckDB grouped queries retain native `ORDER BY`; bar ties use the source
  category expression, nonmissing counts first, and missing last.
- **Visualization ordering:** Altair receives the backend category sequence explicitly and does not
  re-sort categories by its own count order.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy tabulate fixtures agree for numeric,
  text, Decimal, NaN, and missing keys; each Polars operation is independently verified as fallback.
- **User-facing paths:** CLI numeric header output, help text, canonical script replay, and language
  docs cover the contract.
- **Scope control:** no sort syntax, active row-order metadata, arbitrary SQL rewrite, categorical
  ordering, command, or estimator was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Initial ordering executor regressions: 5 passed.
- Final review-fix executor regressions: 9 passed.
- Focused ordering CLI regression: 1 passed; help regression: 1 passed.
- `uv run pytest` — 1,062 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** found Medium exact numeric precision loss and NaN key canonicalization defects.
- **Pass 2:** independently found the same exact precision issue and a Low Polars test-isolation gap.
- **Pass 3:** found Medium Altair re-sorting and NaN cell-key defects plus a Low SPEC wording issue.

Fixed by preserving exact numeric sort values, canonicalizing NaN keys for deduplication and cell
maps, passing explicit backend category order to Altair, isolating Polars grouped operations, and
clarifying deferred arithmetic/order scope in SPEC. No Critical or High findings remain.

## Non-Blocking Follow-Ups

Active row order, `head`/`tail`, arbitrary SQL ordering, categorical ordering, exact arithmetic
widths, overflow diagnostics, randomness, estimation samples, machine output, exit semantics,
lineage, differential assurance, and public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the review-fix commit, update the PR body, mark the PR ready, merge it, then fast-forward
`main` and clean up the feature branch.

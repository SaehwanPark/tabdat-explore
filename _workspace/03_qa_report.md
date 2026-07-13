# QA Report: Phase 24 P0 Missing Predicate Semantics

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, and the product contract
  agree on true/false/missing predicate behavior and aggregate missingness.
- **Backend behavior:** eager/DuckDB and Polars paths agree that drop predicates retain missing
  results while keep predicates exclude them.
- **Existing aggregate behavior:** summarize counts nonmissing numeric values, codebook reports
  missing counts, tabulate's `missing` option includes null categories, and missing bar categories
  render with the stable `<missing>` label.
- **Scope control:** no new missing syntax, null literal, coercion policy, estimator behavior, or
  backend was added.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest tests/test_executor.py -k 'missing_predicates_are_consistent or tabulate_missing_option_controls or all_missing_numeric or phase_24_bar_missing' -q` — 6 passed.
- `uv run pytest tests/test_cli.py -k 'missing_drop_predicate' -q` — 2 passed.
- `uv run pytest` — 984 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six integrated scenarios passed, including exact
  canonical replay.

## PR Review Loop

Three independent review passes completed before merge readiness:

- **Pass 1:** fixed the documented-but-unrendered missing bar category by normalizing it to
  `<missing>` and added an SVG artifact regression. Clarified Polars replace coverage by asserting
  the supported fallback materializes to eager state.
- **Pass 2:** independently confirmed the same fallback evidence gap, then verified the script CLI
  path and added all-missing aggregate and bar-output regressions.
- **Pass 3:** no actionable findings.

No Critical or High findings remain. All Medium and Low findings were addressed and revalidated.

## Non-Blocking Follow-Ups

- Explicit missing predicates/null literals, coercion, arithmetic/categories, ordering/randomness,
  estimation samples, machine output, exit semantics, lineage, differential assurance, and
  public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the reviewed fix commit, mark the PR ready, merge it, then fast-forward `main` and clean up the
feature branch.

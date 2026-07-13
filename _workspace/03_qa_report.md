# QA Report: Phase 24 P0 Missing Predicate Semantics

Status: implementation validation pass; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, and the product contract
  agree on true/false/missing predicate behavior and aggregate missingness.
- **Backend behavior:** eager/DuckDB and Polars paths agree that drop predicates retain missing
  results while keep predicates exclude them.
- **Existing aggregate behavior:** summarize counts nonmissing numeric values, codebook reports
  missing counts, and tabulate's `missing` option includes null categories.
- **Scope control:** no new missing syntax, null literal, coercion policy, estimator behavior, or
  backend was added.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest tests/test_executor.py -k 'missing_predicates_are_consistent or tabulate_missing_option_controls' -q` — 4 passed.
- `uv run pytest tests/test_cli.py -k 'missing_drop_predicate' -q` — 1 passed.
- `uv run pytest` — 981 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six integrated scenarios passed, including exact
  canonical replay.

## PR Review Loop

- Three independent code-review passes will run after the PR is opened.
- Findings, fixes, and final disposition will be recorded here before merge.

## Non-Blocking Follow-Ups

- Explicit missing predicates/null literals, coercion, arithmetic/categories, ordering/randomness,
  estimation samples, machine output, exit semantics, lineage, differential assurance, and
  public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Commit the validated slice, open the PR, and run exactly three independent review passes.

# QA Report: Phase 24 P0 Explicit Missing Predicates

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on `null` literal spelling, null-aware equality/inequality, and deferred
  coercion.
- **Parser to AST:** unquoted `null` becomes a null literal while quoted `` `null` `` remains a
  variable identifier.
- **Backend behavior:** eager, DuckDB-lazy, and Polars-lazy paths agree for explicit missing
  predicates and direct null assignment, including direct `null` row predicates.
- **Failure behavior:** unsupported null arithmetic/function use fails before mutation with a stable
  diagnostic; invalid tabulate conditions fail before Polars-lazy materialization.
- **User-facing paths:** CLI `-c`, script execution, and command help document and exercise the
  contract.
- **Scope control:** no `is null`/function syntax, coercion policy, new command, or estimator was
  added.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest tests/test_parser.py -k 'null_literal' -q` — 1 passed.
- `uv run pytest tests/test_executor.py -k 'explicit_null_predicates or null_literal_rejects' -q` —
  9 passed.
- `uv run pytest tests/test_cli.py -k 'explicit_missing_predicate' -q` — 2 passed.
- `uv run pytest tests/test_help.py -k 'explicit_missing' -q` — 1 passed.
- `uv run pytest tests/test_executor.py -k 'failed_polars_tabulate_null_validation' -q` — 2 passed.
- `uv run pytest` — 999 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six integrated scenarios passed, including exact
  canonical replay.

## PR Review Loop

Three independent review passes completed before merge readiness:

- **Pass 1:** PASS; no actionable cross-boundary findings.
- **Pass 2:** found a Medium atomicity issue where invalid tabulate null conditions materialized
  Polars-lazy state before rejection. Fixed by validating direct and `by:` tabulate conditions before
  fallback materialization, with two state-preservation regressions.
- **Pass 3:** PASS; no actionable release-readiness findings.

No Critical or High findings remain. The single Medium finding was fixed and revalidated.

## Non-Blocking Follow-Ups

- Implicit coercion, broader arithmetic, categories, ordering/randomness, estimation samples,
  machine output, exit semantics, lineage, differential assurance, and public-preview readiness
  remain queued in `SPEC.md`.

## Recommended Next Action

Push the reviewed fix commit, mark the PR ready, merge it, then fast-forward `main` and clean up the
feature branch.

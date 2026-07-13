# QA Report: Phase 24 P0 Explicit Missing Predicates

Status: implementation validation pass; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on `null` literal spelling, null-aware equality/inequality, and deferred
  coercion.
- **Parser to AST:** unquoted `null` becomes a null literal while quoted `` `null` `` remains a
  variable identifier.
- **Backend behavior:** eager, DuckDB-lazy, and Polars-lazy paths agree for explicit missing
  predicates and direct null assignment, including direct `null` row predicates.
- **Failure behavior:** unsupported null arithmetic/function use fails before mutation with a stable
  diagnostic.
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
- `uv run pytest` — 997 passed, 314 existing third-party warnings.
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

- Implicit coercion, broader arithmetic, categories, ordering/randomness, estimation samples,
  machine output, exit semantics, lineage, differential assurance, and public-preview readiness
  remain queued in `SPEC.md`.

## Recommended Next Action

Commit the validated slice, open the PR, and run exactly three independent review passes.

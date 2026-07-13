# QA Report: Phase 24 P0 Identifier Spelling and Quoted Identifiers

Status: implementation validation pass; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, and the product contract
  agree on exact case-sensitive spelling and backtick quoting.
- **Parser to command AST:** quoted whitespace, punctuation, escaped backticks, and quoted `if` are
  preserved as identifier content across targets, lists, expressions, `by`, and Bayes prefixes.
- **Executor/backend behavior:** generated and replaced columns with spaces and capital letters are
  materialized with exact names; a lowercase mismatch remains an unknown-variable failure; Bayes
  formula identifiers are quoted before formula evaluation.
- **User-facing paths:** `-c`, script execution, and Unicode quoted identifiers are covered.
- **Scope control:** SQL quoting, missingness, coercion, successful bare-identifier behavior, and
  estimator semantics remain unchanged.

## Blocking Issues

- None found in implementation validation.

## Validation Evidence

- `uv run pytest tests/test_parser.py -q` — 488 passed.
- `uv run pytest tests/test_executor.py -k 'quoted_identifiers_execute or bayes_formula_identifier' -q` — 2 passed.
- `uv run pytest tests/test_cli.py -k 'quoted_identifier or quoted_unicode_identifier' -q` — 2 passed.
- `uv run pytest` — 976 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six integrated scenarios passed, including exact
  canonical replay.

## PR Review Loop

Three independent review passes completed. All findings were addressed before merge readiness:

- **Pass 1:** fixed quote-aware `by`/Bayes-prefix framing, preserved quoted control-word metadata,
  quoted Bayes formula identifiers, and added an explicit backtick limitation for that backend.
- **Pass 2:** independently confirmed wrapper framing, then fixed bare punctuation boundaries and
  added CLI/script/Unicode acceptance coverage.
- **Pass 3:** fixed the remaining recode structural delimiter check and retained the wrapper/control
  metadata fixes.

No Critical or High findings remain. The two legacy unquoted-punctuation parser fixtures were updated
to the documented backtick syntax, and the final full suite passed.

## Non-Blocking Follow-Ups

- Missing values/coercion, arithmetic/categories, ordering/randomness, estimation samples, machine
  output, exit semantics, lineage, and public-preview assurance remain queued in `SPEC.md`.

## Recommended Next Action

Push the reviewed fix commit, mark the PR ready, merge it, then fast-forward `main` and clean up the
feature branch.

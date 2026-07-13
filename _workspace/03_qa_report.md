# QA Report: Phase 24 P0 Expression Coercion

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, help topics, and the
  product contract agree on numeric, string, boolean, other, and null domains.
- **AST/backend typing:** comparisons, arithmetic, functions, predicates, replacement targets, and
  tabulate inputs enforce the declared domains before execution.
- **Cross-engine behavior:** compatible numeric expressions agree across eager, DuckDB-lazy, and
  Polars-lazy paths; unsafe unsigned/negative combinations are rejected consistently.
- **Failure behavior:** mixed-domain expressions, invalid replacement NULLs, and invalid tabulate
  commands fail before active-dataset mutation or Polars-lazy fallback materialization.
- **User-facing paths:** CLI `-c`, script execution, command help, and documentation cover the
  contract.
- **Scope control:** no new syntax, categorical conversion, string concatenation, command, or
  estimator was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Focused expression executor regressions: 17 passed.
- Focused review-fix executor regressions: 8 passed.
- Focused CLI regressions: 2 passed.
- Focused help regression: 1 passed.
- `uv run pytest` — 1,025 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six integrated scenarios passed, including exact
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** found a Medium direct-null target-type change and a Low missing tabulate-help rule.
  Fixed with typed NULL casts and help documentation/assertion.
- **Pass 2:** found Medium unsigned/negative parity, incomplete tabulate preflight, and direct-null
  type issues; also found Low Arrow/Polars type normalization and help coverage gaps. Fixed with
  deterministic unsigned rejection, complete non-materializing tabulate validation, canonical type
  domains, typed NULL casts, and help updates.
- **Pass 3:** independently confirmed the Medium direct-null type issue and a Low stale “coercion is
  undefined” sentence. Fixed with typed NULL casts and the corrected deliberate-limits text.

No Critical or High findings remain. All Medium and Low findings were fixed and revalidated.

## Non-Blocking Follow-Ups

- Categorical conversion beyond storage normalization, string concatenation, ordering/randomness,
  estimation samples, machine output, exit semantics, lineage, differential assurance, and
  public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the reviewed fix commit, mark the PR ready, merge it, then fast-forward `main` and clean up the
feature branch.

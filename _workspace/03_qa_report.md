# QA Report: Phase 24 P0 Categorical Ordering

Status: three-review pass complete; fixes validated; PR #102 ready for merge

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, tabulate/bar help, command reference,
  and the product contract agree on native scalar order and missing placement.
- **Native values:** numeric labels are ordered numerically, text lexicographically, and booleans
  false before true rather than by rendered text.
- **Missing categories:** tabulate omission/inclusion and bar missing-last display are covered.
- **Bar ties:** descending counts are followed by native category order.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy outputs agree.
- **Scope control:** no category metadata, level syntax, recoding, sort abstraction, relation-order
  rewrite, or estimator behavior was added.
- **Presentation safety:** missing and reserved-looking labels remain distinct in bar charts and wide
  tabulate headers, including multi-key separator collisions.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine categorical regression: 3 passed, each executing a fresh `BarCommand` artifact.
- Collision regressions: bar label and wide tabulate header tests passed.
- CLI regression: 1 passed; focused help regression: 1 passed.
- `uv run pytest` — 1,106 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed on PR #102. All findings were addressed:

- Collision-safe rendering was added for bar labels and wide tabulate headers.
- Fresh per-engine `BarCommand` artifact coverage and stronger CLI assertions were added.
- Command-reference wording and workspace handoff state were corrected.

No fourth review pass is planned.

## Non-Blocking Follow-Ups

Unordered SQL, exact arithmetic widths, overflow diagnostics, randomness, estimation samples, errors
and exits, lineage, differential assurance, and public-preview readiness remain queued in `SPEC.md`
Future.

## Recommended Next Action

Commit and push the validated review fixes, update PR #102, wait for its required checks, merge it to
`main`, delete the local and remote feature branch, and return to the next `SPEC.md` item.

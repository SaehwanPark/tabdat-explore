# Implementation Report: Phase 24 P0 Materialization-Reason Taxonomy

## Contract Consumed

- `_workspace/01_product_command-contract.md` — expanded `status` reason taxonomy.

## Delivered Boundary

- `src/tabdat/executor.py` and `src/tabdat/models.py`
  - Expanded the typed reason union with `eager_operation`.
  - Detects a successful lazy-to-eager active-dataset transition after command execution.
  - Restricts the generic transition category to a prior DuckDB-lazy dataset; Polars remains on
    the specific fallback path.
  - Keeps the specific staged `polars_fallback` reason ahead of the generic transition reason.
  - Preserves success-only and reset precedence from the previous slice.
- `src/tabdat/formatter.py`
  - Maps internal reason values to exact public phrases: `polars fallback`, `eager operation`, and
    `none`.
- `tests/`
  - Covers DuckDB-lazy eager transitions, Polars fallback precedence, source/table resets, CLI and
    script output, and the existing status/operation/failure paths.
- `src/tabdat/help/topics/status.md`, `docs/command-reference.md`, `docs/user-guide.md`,
  `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Documented the taxonomy, examples, limits, acceptance criteria, and validation evidence.

## Implementation Notes By Boundary

- Transition boundary: the executor compares the active dataset mode before and after a successful
  command; source/table reset operations take precedence.
- Reason specificity: a staged Polars fallback is retained instead of being overwritten by the
  generic lazy-to-eager transition category.
- Failure boundary: failed commands do not commit a new reason, using the existing pending metadata
  wrapper.
- Scope: this is a user-visible taxonomy, not a backend-internal materialization trace.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'status or fallback' -q` — passed, 9 tests.
- `uv run pytest tests/test_cli.py -k 'phase_24_status or fallback_reason or eager_operation' -q` — passed, 7 tests.
- `uv run pytest` — passed, 967 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed; all six scenarios passed, including
  canonical replay with exact stdout/table equivalence and 4.324 seconds composite duration.

## Known Limits And Follow-Up Work

- The taxonomy intentionally does not identify backend-internal substeps, timings, or every
  possible materialization cause.
- Full operation lineage, retained estimation samples, machine-readable output, and explain/dry-run
  remain future Phase 24 work.

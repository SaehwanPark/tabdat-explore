# Implementation Report: Phase 24 P0 Canonical Parquet Workflow

## Contract Consumed

- `_workspace/01_product_command-contract.md` — Phase 24 P0 canonical Parquet workflow.

## Files Changed

- `demos/canonical_parquet_eda.td`
  - Added the tracked user-facing workflow using script macros, lazy DuckDB Parquet loading,
    `describe`, `count`, `codebook`, filtering, derivation, overall and grouped summaries,
    `collapse`, and Parquet export.
- `tests/test_canonical_workflow.py`
  - Added a local end-to-end replay test with a temporary Parquet fixture.
  - Verifies identical script transcripts and exported schema/rows across two CLI runs.
- `integrated_testing/run_e2e.py`
  - Added `s6_canonical_parquet_workflow`.
  - Runs the tracked script twice, compares stdout and exported Parquet snapshots, checks the
    expected three-row/four-column output, and records per-run wall-clock metrics.
  - Added duration and metric fields to integrated JSON/Markdown reports.
- `integrated_testing/README.md`, `docs/user-guide.md`, and `docs/e2e_public_dataset_test_plan.md`
  - Published the workflow, invocation, scope, replay contract, and benchmark limitations.
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/00_input/request-summary.md`
  - Recorded the active branch and verification criteria, then moved the verified slice into Past.
- `tests/test_executor.py`
  - Hardened the pre-existing HTML report downsampling test to identify the diagnostic observation
    dataset by fields and separately verify the one-row zero reference line, without depending on
    Altair dataset insertion order.
- `integrated_testing/run_e2e.py`
  - Pins public fixture sources and verifies SHA-256 digests before use.
  - Compares Parquet column names and types, checks expected canonical aggregate values, aggregates
    composite scenario durations, and reports both replay exit codes.

## Implementation Notes By Boundary

- Product/docs: the workflow uses existing command contracts and does not add a new command or
  alter semantics.
- Script/CLI edge: macro expansion and script transcript output remain the existing reproducible
  path; the tracked script is executed directly by the harness.
- Backend/output evidence: the harness reads the exported Parquet through DuckDB and compares
  schema plus sorted rows, keeping file inspection at the integration edge.
- Benchmark: timings measure each `uv run tabdat -f ...` subprocess after dataset preparation;
  no host-independent threshold is asserted.

## Validation Commands And Outcomes

- `uv run pytest tests/test_canonical_workflow.py -q` — passed, 1 test.
- `uv run pytest tests/test_executor.py -k 'estat_report' -q` — passed, 4 tests.
- `uv run pytest` — passed, 947 tests (314 expected third-party warnings).
- `uv run basedpyright src/tabdat/reporting.py integrated_testing/run_e2e.py tests/test_canonical_workflow.py` — passed, 0 errors/warnings/notes.
- `uv run basedpyright` — passed, 0 errors/warnings/notes.
- `uv run ruff check src/tabdat/reporting.py integrated_testing/run_e2e.py tests/test_canonical_workflow.py` — passed.
- `uv run ruff check .` — passed.
- `uv run ruff format --check src/tabdat/reporting.py integrated_testing/run_e2e.py tests/test_canonical_workflow.py` — passed after formatting.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s6_canonical_parquet_workflow` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed; all six scenarios passed.
  - canonical full-run first replay: approximately 2.160 seconds
  - canonical full-run second replay: approximately 2.144 seconds
  - output: 3 rows, 4 columns; exact stdout and table replay match

## Known Limits And Follow-Up Work

- The public Titanic fixture depends on external dataset availability; the local replay test keeps
  command validation independent of that network dependency.
- Timing values are observations and are intentionally not a portable performance gate.
- Execution transparency, cross-command semantic policy, machine-readable output, and dependency
  measurement remain later Phase 24 slices.

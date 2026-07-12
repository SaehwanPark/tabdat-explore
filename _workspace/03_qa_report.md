# QA Report: Phase 24 P0 Canonical Parquet Workflow

Status: pass

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/user-guide.md`, and
  `docs/e2e_public_dataset_test_plan.md` identify the same Phase 24 P0 workflow, expected
  Titanic-shaped input columns, output path/shape, replay checks, and timing non-goal.
- **Contract to tracked script:** `demos/canonical_parquet_eda.td` contains lazy DuckDB loading,
  `describe`, `count`, `codebook`, filtering, derivation, overall/grouped summaries, collapse, and
  export in the contracted order.
- **Script to CLI/parser/executor:** the local replay test and real harness execute the tracked
  script through `tabdat -f`; both runs emit the expected transcript and exit successfully.
- **Executor/backend to evidence:** the harness reads the exported Parquet through DuckDB and
  compares column names and sorted rows between replays; it does not infer equivalence from
  stdout alone.
- **Benchmark/reporting:** `ScenarioResult` records per-process wall-clock durations and canonical
  output metrics in JSON/Markdown reports; no timing threshold is asserted.
- **Existing reporting behavior:** the Phase 13 HTML report downsampling regression is covered by
  its focused tests after the narrow Altair serialization fix.

## Blocking Issues

- None.

## Non-Blocking Follow-Ups

- Public dataset acquisition remains network-dependent in the integrated harness; the local
  temporary-fixture replay test provides an offline command-contract check.
- Cross-command semantic policy, execution transparency, machine-readable output, and dependency
  measurement remain intentionally queued Phase 24 work.
- Benchmark timings are host-dependent observations rather than release thresholds.

## Validation Evidence

- `uv run pytest` — 947 passed, 314 third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — all six scenarios passed.
- Canonical replay evidence: exact stdout match, exact exported table match, 3 output rows, 4
  output columns; observed first/replay CLI timings approximately 2.166s/2.166s in the full run.

## Recommended Next Action

Proceed to the three independent code-review passes, then use the documented PR/merge handoff.

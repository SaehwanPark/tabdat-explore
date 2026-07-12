# Product Contract: Phase 24 P0 — Canonical Parquet Workflow

## Request Summary

Publish one runnable, reproducible terminal EDA journey and make its integrated validation output
include repeatability and timing evidence.

## Roadmap Phase

Phase 24 P0, workstream 1: product-center stabilization and public-preview readiness.

## Product Outcome

TabDat demonstrates that it is the fastest, clearest, and most reproducible terminal workflow for
first-pass exploration of modern tabular data. Conventional statistics remain available, while
specialized integrations no longer determine the installation or product narrative of the core.

## Published Workflow

Tracked script: `demos/canonical_parquet_eda.td`.

The script expects a Titanic-shaped Parquet dataset with `age`, `fare`, `sibsp`, `parch`, and
`class` columns. It performs these steps in order:

1. Set source and output paths with script macros.
2. Load the source lazily through DuckDB.
3. Inspect structure and row count with `describe` and `count`.
4. Inspect missingness and representative values with `codebook`.
5. Filter adults and derive `family_size`.
6. Run overall and `by class:` summaries.
7. Collapse the transformed data to class-level means.
8. Export the transformed summary as Parquet.

Canonical invocation:

```bash
uv run tabdat -f demos/canonical_parquet_eda.td
```

## Integrated Benchmark Contract

The `s6_canonical_parquet_workflow` harness scenario must:

- use the existing Titanic public fixture converted to Parquet;
- run the same tracked script twice in separate CLI processes;
- require exit code `0` and empty stderr for both runs;
- require both runs to emit the same stdout;
- require both exported Parquet tables to have the same schema and rows, with three class rows and
  four output columns;
- record the wall-clock duration of each CLI run in `reports/latest/results.json` and the summary;
- treat timings as observations, not a host-independent pass/fail threshold.

## Acceptance Criteria

- [x] The tracked script contains lazy Parquet load, inspection, missingness, transformation,
  grouped summary, collapse, and export steps.
- [x] The user guide explains the expected input columns, invocation, and output artifact.
- [x] The integrated scenario verifies deterministic replay and exported-table equivalence.
- [x] The integrated report records timing evidence for both replays.
- [x] The scenario passes from a synced environment without modifying source or test fixtures.

## Ordered Workstreams

1. Publish one measured end-to-end Parquet workflow as the product acceptance journey.
2. Specify cross-command language semantics and stable error/exit behavior.
3. Add execution transparency (`status`/`explain`) before expanding the command catalog.
4. Add deterministic machine-readable output and command discovery for agents and scripts.
5. Strengthen golden, execution-mode, backend-differential, and estimator-reference testing.
6. Measure startup/install costs, then design optional dependency and adapter boundaries.
7. Resolve public naming and preview versioning using availability and migration evidence.
8. Separate durable architecture, capability status, history, and ADR responsibilities.

## Later Phase 24 Gate (unchanged)

- A fresh user can install the core workflow without R, Bayesian, spatial, or ML runtimes.
- The canonical workflow runs interactively and as a deterministic `.td` script.
- Execution mode and materialization boundaries are inspectable.
- Core command semantics and machine-readable errors are documented and tested.
- Backend and eager/lazy overlaps have explicit equivalence coverage.
- Statistical support claims link to a support matrix and trusted-reference fixtures.
- Public naming, dependency layering, and versioning decisions are recorded as ADRs.

## Non-Goals For This Slice

- Implementing `status`/`explain`, machine-readable output, semantic policy changes, or dependency
  layering.
- Adding estimators or broad connectors before the stabilization gate.
- Making timing thresholds part of the public command contract.

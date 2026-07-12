# Request Summary: Phase 24 Canonical Parquet Workflow

## Goal

Implement the first Phase 24 stabilization slice: publish and measure one canonical Parquet-first
workflow that demonstrates TabDat's core terminal EDA path before further estimator expansion.

## Phase Fit

Phase 24 P0 product-center stabilization. This is the first implementation slice after the
feedback-driven roadmap reprioritization.

## Touched Surfaces

- `demos/canonical_parquet_eda.td`: reusable user-facing workflow
- `docs/user-guide.md`: canonical workflow instructions and scope
- `docs/e2e_public_dataset_test_plan.md`: scenario and acceptance evidence
- `integrated_testing/run_e2e.py`: deterministic replay and timing checks
- `integrated_testing/README.md` and `RUN_REPORT.md`: harness usage and measured result
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: SDD state and delivery evidence

## Assumptions

- Existing `use`, inspection, transformation, grouped-summary, and export contracts are sufficient;
  no runtime command semantics need to change.
- The integrated harness may use the existing public Titanic sample and converts it to Parquet as
  an external fixture; the tracked workflow documents its expected schema.
- Timing is observational evidence rather than a machine-specific performance threshold.

## Non-Goals

- Adding `status`, `explain`, JSON output, or new command semantics.
- Adding estimator families, broader connectors, or dependency-layer changes.
- Treating public dataset acquisition or host-specific timing as a product guarantee.

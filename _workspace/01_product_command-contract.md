# Product Contract: Phase 24 — Stabilization and Public Preview

## Product Outcome

TabDat demonstrates that it is the fastest, clearest, and most reproducible terminal workflow for
first-pass exploration of modern tabular data. Conventional statistics remain available, while
specialized integrations no longer determine the installation or product narrative of the core.

## Ordered Workstreams

1. Publish one measured end-to-end Parquet workflow as the product acceptance journey.
2. Specify cross-command language semantics and stable error/exit behavior.
3. Add execution transparency (`status`/`explain`) before expanding the command catalog.
4. Add deterministic machine-readable output and command discovery for agents and scripts.
5. Strengthen golden, execution-mode, backend-differential, and estimator-reference testing.
6. Measure startup/install costs, then design optional dependency and adapter boundaries.
7. Resolve public naming and preview versioning using availability and migration evidence.
8. Separate durable architecture, capability status, history, and ADR responsibilities.

## Acceptance Gate

- A fresh user can install the core workflow without R, Bayesian, spatial, or ML runtimes.
- The canonical workflow runs interactively and as a deterministic `.td` script.
- Execution mode and materialization boundaries are inspectable.
- Core command semantics and machine-readable errors are documented and tested.
- Backend and eager/lazy overlaps have explicit equivalence coverage.
- Statistical support claims link to a support matrix and trusted-reference fixtures.
- Public naming, dependency layering, and versioning decisions are recorded as ADRs.

## Non-Goals

- Removing already shipped statistical commands during planning.
- Adding estimators or broad connectors before the stabilization gate.
- Prematurely creating multiple repositories or distributions.

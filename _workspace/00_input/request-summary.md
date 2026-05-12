# Phase 13 Slice 1 Request Summary

## Goal

Move to the next planned phase per `SPEC.md` by implementing a bounded first Phase 13 linear-econometrics slice, then ship it through branch checkpoints, documentation, and a ready-for-review PR.

## Phase Fit

- Gate interpretation: roadmap phases 0-12 are complete and Phase 13 is next.
- In-scope phase: Phase 13 (slice 1), Python-first approach order.

## Scope

- Add `regress <y> <xvars>[, robust cluster(<var>) noconstant]`.
- Add `predict <newvar>[, xb residuals]` using the latest in-session regression model.
- Use `statsmodels` first (per phase policy).
- Add focused parser/executor/backend/CLI/shell coverage.
- Keep FP-style explicit state boundaries and typed models.
- Update `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and `README.md`.
- Produce `_workspace` implementation and QA reports.
- Open one ready-for-review PR from a temporary branch with meaningful checkpoint commits.

## Non-Goals

- No WLS/GLS in this slice.
- No regression `if` filtering or weights in this slice.
- No HTML report UI for regression diagnostics.
- No Phase 14+ model work.

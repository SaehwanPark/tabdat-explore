# Phase 13 Slice 2 Request Summary

## Goal

Identify the next implementation target from `SPEC.md`, complete any prerequisite work before advancing
phases, then implement the next bounded development slice with branch checkpoints, documentation,
and a ready-for-review PR.

## Phase Fit

- Gate interpretation: prior phases are treated as complete by documented exit gates.
- In-scope phase: Phase 13 core linear econometrics (slice 2).
- Out-of-scope phase: Phase 14+ for this task.

## Scope

- Extend `regress` with weighted estimator options:
  - `wls(<weight_var>)`
  - `gls(<sigma_var>)`
- Keep `predict` compatible with the latest weighted or unweighted regression model state.
- Allow covariance mode combinations (`robust` and `cluster(...)`) with OLS/WLS/GLS.
- Enforce positive retained-row values for WLS weights and GLS sigma inputs.
- Keep Python-first implementation order through `statsmodels`.
- Add focused parser/executor/CLI/shell coverage and synchronize SDD docs.

## Non-Goals

- No Phase 14 work.
- No broad linear diagnostics expansion in this slice.
- No new top-level commands (`wls`/`gls`) outside `regress` options.
- No regression `if` grammar expansion.

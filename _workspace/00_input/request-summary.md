# Phase 13 Slice 3 Request Summary

## User Goal

Complete Phase 13 by implementing the remaining core linear diagnostics slice after prior `regress` and `predict` slices.

## Scope

- In-scope phase: Phase 13 core linear econometrics (slice 3).
- Add post-estimation diagnostics command surface:
  - `estat residuals`
  - `estat ovtest`
  - `estat vif`
- Keep existing `regress` and `predict` behavior unchanged except for diagnostics integration.
- Use the Phase 13 implementation order:
  1. Python libraries first (`statsmodels`).
  2. R via `rpy2` only when Python is insufficient.
  3. Narrow lower-level fallback only when both prior approaches fail.

## Constraints

- Preserve Stata-inspired command style.
- Keep changes as a bounded vertical slice across parser, executor, CLI/shell UX, docs, and tests.
- Keep deterministic terminal output and focused validation evidence.

## Non-goals

- No IV/panel/nonlinear model work (Phase 14+).
- No broad parser redesign.
- No interactive HTML diagnostics in this slice.

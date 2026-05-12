# Phase 14 Slice 2+3 Request Summary

## User Goal

Implement Phase 14 Slice 2 and, if feasible in the same bounded branch, one additional Phase 14
slice while following `SPEC.md` approach-order policy, creating checkpoint commits, updating SDD
artifacts, and opening a review-ready PR.

## Scope

- Phase 14 Slice 2:
  - add IV diagnostics through `estat firststage` and `estat overid` after `ivregress`
- Phase 14 Slice 3 (conditional on Slice 2 success):
  - add panel starter commands via `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]`
  - add `estat hausman` for matching FE/RE fits

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to vertical-slice surfaces.
- Keep existing `regress`/`predict`/`estat residuals|ovtest|vif` behavior stable.

## Non-goals

- No broad panel-workflow redesign.
- No nonlinear models.
- No R fallback adapter work while Python-first coverage is sufficient.

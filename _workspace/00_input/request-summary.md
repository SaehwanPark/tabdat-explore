# Phase 14 Slices 10-11 Request Summary

## User Goal

Resume development from the latest checkpoint by delivering remaining meaningful Phase 14 slices
with checkpoint commits, updated SDD/handoff artifacts, and a ready-for-review PR.

## Scope

- Phase 14 Slice 10:
  - add IV-GMM support through existing command surface:
    - `ivregress gmm`
  - keep existing IV option surface (`endog`, `iv`, `robust`, `cluster`, `noconstant`)
  - preserve deterministic `estat overid` behavior for both `2sls` and `gmm`
- Phase 14 Slice 11:
  - extend `estat endogenous` to support prior `ivregress 2sls`
  - preserve existing `estat endogenous` behavior after `cfregress`

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one PR with meaningful checkpoint commits.
- Keep existing Phase 13/14 command behavior stable unless explicitly extended above.

## Non-goals

- No new nonlinear (Phase 15) estimators.
- No broad panel workflow redesign.
- No R adapter work while Python-first coverage is sufficient.
- No new command families outside the existing `ivregress`/`estat` surfaces.

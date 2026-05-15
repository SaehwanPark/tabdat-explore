# Phase 15 Slice 4-5 Request Summary

## User Goal

Resume development from the latest checkpoint by implementing two remaining meaningful Phase 15
slices in one bounded PR with checkpoint commits, updated SDD artifacts, and a ready-for-review PR.

## Scope

- Phase 15 Slice 4:
  - add bounded nonlinear prediction routing for binary-choice models
  - extend command surface:
    - `predict <newvar>[, xb residuals pr]`
  - `pr` returns fitted probabilities after `logit`/`probit`
- Phase 15 Slice 5:
  - add bounded limited-dependent estimator entrypoint via Tobit
  - command surface:
    - `tobit <y> <xvars>, ll(<num>) [ul(<num>) robust cluster(<var>) noconstant]`

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one PR with meaningful checkpoint commits.
- Keep existing Phase 13/14/15 command behavior stable unless explicitly extended above.

## Non-goals

- No nonlinear binary residual diagnostics expansion.
- No sample-selection (`heckman`) command family in this PR.
- No broad nonlinear-regression command family in this PR.

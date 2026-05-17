# Phase 17 Slice 1 Request Summary

## User Goal

Resume development from the latest merged checkpoint by moving from completed Phase 16 into the
next meaningful slice, with checkpoint commits, full validation, updated SDD/docs, and a
ready-for-review PR.

## Scope

- Resume from latest merged checkpoint on `main` (Phase 16 complete).
- Phase 17 Slice 1:
  - add bounded quantile-regression entrypoint
  - command surface:
    - `qreg <y> <xvars>[, quantile(<0,1>) robust noconstant]`
  - post-estimation:
    - `predict <newvar>[, xb residuals]` after `qreg`
    - `estat residuals` after `qreg`

## Constraints

- Keep deterministic output and strict option validation.
- Preserve existing `regress`/`predict`/`estat` boundaries unless explicitly extended above.
- Keep implementation as one bounded PR with meaningful checkpoint commits.

## Non-goals

- No panel-GMM or causal command families in this slice.
- No `qreg` clustered covariance mode in this slice.
- No `estat` expansion for `qreg` beyond `residuals`.

# Phase 16 Slice 2 Request Summary

## User Goal

Resume development from the latest merged checkpoint by moving from completed Phase 15 to the next
phase with meaningful checkpoint commits, complete documentation (including in-app help), and a
ready-for-review PR.

## Scope

- Resume from latest merged checkpoint on `main` (Phase 16 Slice 1 complete).
- Phase 16 Slice 2:
  - add bounded negative-binomial count-model entrypoint
  - command surface:
    - `nbreg <y> <xvars>[, robust cluster(<var>) noconstant]`
  - post-estimation:
    - `predict <newvar>[, xb residuals]` after `nbreg`
    - `estat gof` after `nbreg`

## Constraints

- Keep deterministic output and strict option validation.
- Preserve existing model-family behavior unless explicitly extended above.
- Keep implementation as one bounded PR with meaningful checkpoint commits.

## Non-goals

- No zero-inflated, hurdle, multinomial, or survival families.
- No new `predict` option keyword additions (for example, no `mu`).

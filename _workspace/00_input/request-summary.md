# Phase 16 Slice 3 Request Summary

## User Goal

Resume development from the latest merged checkpoint by moving from completed Phase 16 Slice 2 to
the next phase slice with meaningful checkpoint commits, complete documentation (including in-app
help), and a ready-for-review PR.

## Scope

- Resume from latest merged checkpoint on `main` (Phase 16 Slice 2 complete).
- Phase 16 Slice 3:
  - add bounded zero-inflated count-model entrypoints
  - command surface:
    - `zip <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`
    - `zinb <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`
  - post-estimation:
    - `predict <newvar>[, xb residuals]` after `zip` and `zinb`
    - `estat gof` after `zip` and `zinb`

## Constraints

- Keep deterministic output and strict option validation.
- Preserve existing model-family behavior unless explicitly extended above.
- Keep implementation as one bounded PR with meaningful checkpoint commits.

## Non-goals

- No hurdle or finite-mixture model families.
- No new `predict` option keyword additions (for example, no `mu`).

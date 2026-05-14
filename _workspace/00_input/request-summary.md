# Phase 15 Slice 2-3 Request Summary

## User Goal

Resume development from the latest checkpoint by implementing remaining meaningful Phase 15 slices
in one bounded PR with checkpoint commits, updated SDD artifacts, and a ready-for-review PR.

## Scope

- Phase 15 Slice 2:
  - add bounded nonlinear binary-choice estimation via `probit`
  - command surface:
    - `probit <y> <xvars>[, robust cluster(<var>) noconstant]`
- Phase 15 Slice 3:
  - add bounded post-estimation marginal effects via `estat margins`
  - available after successful `logit` or `probit`

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one PR with meaningful checkpoint commits.
- Keep existing Phase 13/14 command behavior stable unless explicitly extended above.

## Non-goals

- No nonlinear `predict` expansion in this slice pair.
- No limited-dependent command families (`tobit`, `truncated`, `sample selection`) in this PR.
- No R adapter work while Python-first coverage is sufficient.

# Phase 15 Slice 6 Request Summary

## User Goal

Resume development from the latest merged checkpoint by implementing one bounded Phase 15 slice
(sample selection / Heckman), with checkpoint commits, updated SDD artifacts, and a ready-for-review PR.

## Scope

- Phase 15 Slice 6:
  - add bounded sample-selection estimator entrypoint via Heckman
  - command surface:
    - `heckman <y> <xvars>, selectdep(<var>) select(<vars>) [robust cluster(<var>) noconstant]`

## Constraints

- Keep deterministic behavior and strict option validation, consistent with existing estimator families.
- Use bounded `rpy2` integration for this slice (R `sampleSelection`) and map backend failures to a
  deterministic public error.
- Keep behavior deterministic and bounded to one PR with meaningful checkpoint commits.
- Keep existing Phase 13/14/15 command behavior stable unless explicitly extended above.

## Non-goals

- No broad nonlinear-regression command family in this PR.
- No truncated-regression command family in this PR.
- No `predict`/`estat` extension for sample-selection in this PR.

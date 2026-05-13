# Phase 14 Slice 6 Request Summary

## User Goal

Resume development from the latest checkpoint by delivering the next bounded Phase 14 slice with
checkpoint commits, updated SDD/handoff artifacts, and a ready-for-review PR.

## Scope

- Phase 14 Slice 6:
  - add control-function prediction support through existing command surface:
    - `predict <newvar>`
    - `predict <newvar>, residuals`
  - route prediction state from prior `cfregress` without changing `predict` syntax/options

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one vertical-slice surface.
- Keep existing `regress`/`ivregress`/`xtreg`/`xtdata`/`estat` Phase 14 behavior stable.

## Non-goals

- No new `estat` diagnostics in this slice.
- No new `predict` syntax or option surface.
- No broad panel-workflow redesign.
- No nonlinear estimators.
- No R fallback adapter work while Python-first coverage is sufficient.

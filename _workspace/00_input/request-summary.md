# Phase 14 Slice 4 Request Summary

## User Goal

Resume development from the last checkpoint by delivering the next bounded Phase 14 slice with
checkpoint commits, updated SDD/handoff artifacts, and a ready-for-review PR.

## Scope

- Phase 14 Slice 4:
  - add panel-indexing transforms through `xtdata <varlist>, within|between`
  - require prior panel metadata from `panel <id_var> <time_var>`
  - keep deterministic row-preserving transformed-column behavior

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one vertical-slice surface.
- Keep existing `ivregress`/`xtreg`/`estat` Phase 14 behavior stable.

## Non-goals

- No control-function entry points in this slice.
- No broad panel-workflow redesign.
- No nonlinear estimators.
- No R fallback adapter work while Python-first coverage is sufficient.

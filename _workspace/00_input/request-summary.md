# Phase 17 Slice 3 Request Summary

## User Goal

Resume development from the latest merged checkpoint by continuing Phase 17 with one bounded
combined slice that adds a dynamic-panel starter command and a DID post-estimation diagnostic.

## Scope

- Resume from latest checkpoint on `main` (Phase 17 Slice 2 complete).
- Phase 17 Slice 3:
  - add bounded dynamic-panel starter semantics:
    - `xtabond <y> [xvars] [, robust]`
  - require prior `panel <id_var> <time_var>` metadata
  - add DID post-estimation diagnostics:
    - `estat did` after successful `did`

## Constraints

- Keep deterministic output and strict option/guard validation.
- Preserve existing estimator-family boundaries outside the explicit `xtabond` + `estat did` addition.
- Keep implementation as one bounded PR with meaningful checkpoint commits.

## Non-goals

- No `xtabond` lag-depth option surface in this slice.
- No `predict` support after `xtabond` in this slice.
- No system-GMM or broader dynamic-panel families in this slice.

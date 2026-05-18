# Phase 17 Slice 4 Request Summary

## User Goal

Resume development from the latest merged checkpoint by continuing Phase 17 with one bounded
combined slice that expands dynamic-panel controls and DID post-estimation diagnostics.

## Scope

- Resume from latest checkpoint on `main` (Phase 17 Slice 3 complete).
- Phase 17 Slice 4:
  - expand bounded dynamic-panel starter semantics:
    - `xtabond <y> [xvars] [, robust lags(#) instlag(#)]`
  - preserve required prior `panel <id_var> <time_var>` metadata
  - expand DID post-estimation diagnostics:
    - richer deterministic `estat did` rows after successful `did`

## Constraints

- Keep deterministic output and strict option/guard validation.
- Preserve existing estimator-family boundaries outside explicit `xtabond` and `estat did` changes.
- Keep implementation as one bounded PR with meaningful checkpoint commits.

## Non-goals

- No system-GMM or broader dynamic-panel model families in this slice.
- No new DID estimators beyond bounded TWFE starter and diagnostics expansion.
- No `predict` support after `xtabond` in this slice.

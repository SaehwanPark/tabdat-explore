# Phase 17 Slice 2 Request Summary

## User Goal

Resume development from the latest merged checkpoint by continuing Phase 17 with one bounded causal
slice, plus checkpoint-quality validation and documentation.

## Scope

- Resume from latest checkpoint on `main` (Phase 17 Slice 1 complete).
- Phase 17 Slice 2:
  - add bounded DID command semantics:
    - `did <y> [controls], treat(<var>) post(<var>) [robust]`
  - require prior `panel <id_var> <time_var>` metadata
  - add post-estimation prediction support:
    - `predict <newvar>[, xb]` after `did`

## Constraints

- Keep deterministic output and strict option/guard validation.
- Preserve existing estimator-family boundaries outside the explicit `did` + `predict xb` addition.
- Keep implementation as one bounded PR with meaningful checkpoint commits.

## Non-goals

- No dynamic-panel GMM command in this slice.
- No `estat` expansion for DID diagnostics in this slice.
- No `did` clustered covariance support in this slice.

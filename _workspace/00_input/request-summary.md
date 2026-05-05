# Phase 9 Request Summary

## Goal

Move from the completed Phase 8 scripting slice into Phase 9 configuration and persistence.

## Requested Workflow

- Begin on a temporary branch.
- Commit meaningful checkpoints during implementation.
- Document the completed work carefully.
- Open a PR when done.

## Phase Fit

Phase 9 in `docs/dev_phase.md` covers predictable environment behavior, runtime configuration,
plot defaults, and persistence of session-local transformations.

## Touched Surfaces

- Parser and command models for `set`, `save`, and `export`.
- Executor session state and config updates.
- DuckDB backend row counting and Parquet writes.
- Visualization artifact path defaults.
- CLI config loading and script metadata.
- Formatter output, tests, README, SDD docs, and handoff artifacts.

## Assumptions

- Implement the full Phase 9 vertical slice: config, runtime settings, plot defaults, and Parquet
  persistence.
- Project-local `.tabdat.toml` and explicit `--config <path>` are enough for this slice.
- `save` and `export` are aliases that write local Parquet only.
- Generated plot names remain stable and may overwrite; explicit `saving(...)` is the reproducible
  escape hatch.

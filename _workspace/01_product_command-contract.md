# Phase 9 Configuration And Persistence Contract

## Roadmap Phase

Phase 9: Configuration & Environment.

## Config Loading

- At startup, TabDat loads `.tabdat.toml` from the current working directory if present.
- `--config <path>` loads an explicit TOML config file and takes the place of `.tabdat.toml`.
- Supported keys:
  - `graph_format = "svg" | "png"`
  - `artifact_dir = "<path>"`
  - `graph_open = true | false`
- Unknown keys, missing config files, invalid TOML, and invalid values are user-facing errors.

## `set`

Syntax:

```text
set graph_format svg
set graph_format png
set artifact_dir artifacts
set graph_open on
set graph_open off
```

- Updates runtime config for the current executor session.
- Affects later commands in the same shell, script, or repeated `-c` command run.
- Prints `Set <name>: <value>`.

## Plot Defaults

- Default plot paths use `<artifact_dir>/plots/<command>-<vars>.<graph_format>`.
- Explicit `saving(...)` keeps overriding directory and extension.
- Interactive shell auto-open respects `graph_open`.
- Batch `-c` and script runs do not auto-open plots.
- Generated plot names are stable and may overwrite existing artifacts.

## `save` / `export`

Syntax:

```text
save output.parquet
save output.parquet, replace
export output.parquet
export output.parquet, replace
```

- Requires an active dataset.
- Writes the active relation to local Parquet.
- Refuses to overwrite existing files unless `replace` is supplied.
- Creates parent directories when needed.
- Prints `Saved: <path> (N rows, M columns)`.

## Lazy Row Count Cleanup

- Lazy `use` validates readability and schema without a load-time full `count(*)`.
- Lazy load output displays an unknown row count until a live count or materializing transform runs.
- `count` always queries the active relation live.

## Non-Goals

- No user-level config search path.
- No CSV, Feather, or Arrow export in this slice.
- No named table registry.
- No timestamped plot naming by default.

## Acceptance Criteria

- Parser tests cover valid and invalid `set`, `save`, and `export`.
- Executor/backend tests cover config mutation, plot defaults, live lazy counts, and Parquet writes.
- CLI tests cover explicit config loading, runtime settings, save output, and invalid config errors.
- Full validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`

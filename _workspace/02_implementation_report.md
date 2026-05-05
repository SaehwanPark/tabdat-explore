# Phase 9 Implementation Report

## Summary

Implemented Phase 9 configuration and persistence on branch
`codex/tmp-phase9-config-persistence`.

## Implemented Behavior

- Added typed runtime config with defaults for graph format, artifact directory, and graph open.
- Added `.tabdat.toml` auto-loading and `--config <path>`.
- Added `set graph_format`, `set artifact_dir`, and `set graph_open`.
- Made generated plot paths config-aware.
- Preserved script and `-c` non-opening plot behavior while making interactive open respect
  `graph_open`.
- Added `save` and `export` for local Parquet persistence with `replace` overwrite control.
- Changed lazy `use` to avoid load-time full row counts.
- Changed `count` to query the active relation live.

## Files Changed

- `src/tabdat/config.py`
- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/executor.py`
- `src/tabdat/backend.py`
- `src/tabdat/visualization.py`
- `src/tabdat/formatter.py`
- `src/tabdat/cli.py`
- `src/tabdat/shell.py`
- focused parser, executor, and CLI tests
- README, SDD docs, and workspace artifacts

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

Focused validation passed after implementation. Final validation is recorded in the delivery
summary.

## Dogfood

Ran a full script flow with `use`, `set`, `keep if`, `count`, `histogram`, and `save`:

```text
uv run tabdat -f /tmp/tabdat_phase9_dogfood.td
```

The run produced a PNG plot under `/tmp/tabdat_phase9_artifacts/plots/` and a filtered Parquet
dataset at `/tmp/tabdat_phase9_filtered.parquet`.

## Known Limits

- Config search is project-local or explicit only.
- Persistence supports Parquet only.
- Generated plot names are stable and may overwrite previous generated artifacts.
- `engine=polars` remains experimental metadata; execution still uses the DuckDB relation boundary.

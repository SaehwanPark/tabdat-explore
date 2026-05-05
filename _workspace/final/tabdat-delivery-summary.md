# Phase 9 Delivery Summary

## Summary

Implemented Phase 9 configuration and persistence on branch
`codex/tmp-phase9-config-persistence`.

## Changed Behavior

- `.tabdat.toml` loads automatically from the current working directory.
- `--config <path>` loads an explicit TOML config.
- `set graph_format`, `set artifact_dir`, and `set graph_open` update runtime behavior.
- Default plot paths use `<artifact_dir>/plots/<command>-<vars>.<graph_format>`.
- Lazy `use` no longer performs a load-time full row count.
- `count` now queries the active relation live.
- `save` and `export` persist the active dataset to local Parquet, with `replace` required for
  overwrites.
- Script metadata now includes relevant config values.

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run tabdat -f /tmp/tabdat_phase9_dogfood.td`

## Known Limits

- Config file discovery is limited to `.tabdat.toml` in the current working directory unless
  `--config` is supplied.
- Persistence supports `.parquet` only.
- Generated plot filenames are stable and can overwrite prior generated plots.
- No named table registry yet.

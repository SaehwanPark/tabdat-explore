# Phase 11 Script Primitives Implementation Report

## Summary

Implemented the next unfinished Phase 11 reproducibility primitive slice on branch
`codex/tmp-phase11-script-primitives`.

## Contract Consumed

`_workspace/01_product_command-contract.md` defines:

- script-only `seed <integer>`
- script-only `let <name> = <value>`
- `$name` macro expansion in later script entries and nested `run` scripts

## Implementation Notes

- Added typed script directive and context models in `src/tabdat/script.py`.
- Added macro expansion and directive parsing helpers with line-numbered `ScriptError` diagnostics.
- Scoped macro and seed state to one top-level script run while sharing it with nested `run`
  scripts.
- Updated CLI script execution to expand macros before echoing and executing commands.
- Added script metadata output for current seed state.
- Added focused script helper and CLI coverage.
- Updated SPEC, ARCHITECTURE, CHANGELOG, README, and workspace artifacts.

## Validation

- `uv run pytest tests/test_script.py tests/test_cli.py`
- `uv run mypy`
- `uv run ruff check src/tabdat/script.py src/tabdat/cli.py tests/test_script.py tests/test_cli.py`

Full validation is recorded in the delivery summary after final checks.

## Known Limits

- `seed` records deterministic metadata only; no random command behavior exists yet.
- Macros are plain text replacements with no quoting, escaping, overwrite, or unset support.
- Script loops, conditionals, inline comments, remote access, and Phase 12 estimation substrate
  work were not added.

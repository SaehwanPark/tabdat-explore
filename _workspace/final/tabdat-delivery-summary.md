# Phase 11 Script Primitives Delivery Summary

## Summary

Implemented Phase 11 script-local seed and macro primitives on branch
`codex/tmp-phase11-script-primitives`.

## Changed Behavior

- `seed <integer>` is available as a script-only directive and records deterministic script-run
  metadata.
- `let <name> = <value>` is available as a script-only directive and defines a plain text macro.
- `$name` macro references expand in later script entries and nested `run` scripts before command
  parsing or execution.
- Each top-level script run starts with empty macro and seed state; nested scripts share parent
  state.
- Script failures for invalid directives or undefined macros include source file and line number.

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Known Limits

- `seed` is metadata-only until future random, simulation, or resampling commands exist.
- Macros are plain text replacements with no quoting, escaping, overwrite, or unset behavior.
- Script loops, conditionals, inline comments, remote access, and Phase 12 estimation substrate
  work remain out of scope.

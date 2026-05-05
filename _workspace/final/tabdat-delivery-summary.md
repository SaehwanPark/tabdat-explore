# Phase 8 Delivery Summary

## Summary

Implemented Phase 8 scripting and reproducibility on branch `codex/phase8-scripting-repro`.

## Changed Behavior

- `tabdat -f <script>` runs a TabDat script file.
- `tabdat <script>` runs a positional TabDat script file.
- `run <script>` runs a script from the current session, including nested scripts.
- Scripts support blank lines, whole-line `#` comments, one command per line, and multiline
  `sql """..."""` blocks.
- Script output includes deterministic metadata and `. <command>` echoes.
- Script failures include file and line number diagnostics and return exit code `1`.
- Script plot commands save artifacts without auto-opening them.
- Docs now mark `engine=polars` as experimental and document lazy materialization limits.

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Known Limits

- No macros, loops, inline comments, or script-level conditionals.
- No config file or persistent export behavior.
- Polars-native command execution is not implemented.

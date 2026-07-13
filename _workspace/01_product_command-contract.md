# Product Contract: Phase 24 P1 — Structured JSON Syntax Preview

## Request Summary

Expose a syntax-only machine-readable preview for exactly one batch command without executing it,
creating a session, or reading data.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Invocation Rules

- `tabdat --json --explain -c "summarize age"` emits exactly one compact deterministic success
  envelope.
- The envelope uses `schema_version: 1`, stable `result_type: "CommandExplainResult"`, and a `data`
  payload containing `command_type: "SummarizeCommand"` and `execution: "not_run"`.
- `command_type` is the existing parsed command dataclass name. This contract does not claim command
  effect classification, option expansion, state planning, or execution equivalence.
- Exactly one `-c/--command` is required. Parse failures emit one existing `ParseError` JSON
  envelope, retain the existing human stderr message, and exit with status `1`.
- Preview routing occurs before config or `Executor` construction, reads no dataset, changes no
  session state, and materializes nothing. Existing command execution, terminal output, interactive
  behavior, and JSON envelopes remain unchanged.
- `--explain` without `--json`, with zero/multiple `-c`, combined with `-f`, a positional script,
  `--list-commands`, or `--help-topic`, and use in an interactive session are rejected clearly with
  existing CLI usage semantics.

## Examples

Valid:

```bash
uv run tabdat --json --explain -c "summarize age"
```

Expected shape:

```json
{"data":{"command_type":"SummarizeCommand","execution":"not_run"},"result_type":"CommandExplainResult","schema_version":1}
```

Syntax failure:

```bash
uv run tabdat --json --explain -c "not_a_tabdat_command"
```

Expected behavior: stderr retains the existing `Error: unknown command: not_a_tabdat_command`, stdout
contains one `ParseError` envelope, and the process exits with status `1`.

## Acceptance Criteria

- [x] One valid versioned success envelope reports the parsed command type and `not_run` execution.
- [x] Preview parses exactly one `-c` command without config/Executor/data/session side effects.
- [x] Syntax failures emit one stable JSON error envelope with exit status `1` and unchanged stderr.
- [x] Incompatible invocation combinations fail clearly without contaminating JSON output or changing
  existing behavior.
- [x] Existing command execution, terminal output, interactive behavior, and JSON schemas remain
  unchanged.
- [x] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Command execution, effect classification, estimates, state/resource plans, scripts, multiple
  commands, option/argument schemas, catalog examples, plugin discovery, interactive JSON mode, full
  dry-run/explain behavior, repair diagnostics, new syntax, or new exit codes.

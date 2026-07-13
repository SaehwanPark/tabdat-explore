# Product Contract: Phase 24 P1 — Structured JSON Help-Topic Retrieval

## Request Summary

Expose one existing in-app help topic through the JSON interface without creating a session or
executing data commands.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Invocation Rules

- `tabdat --json --help-topic summarize` emits exactly one compact deterministic success envelope.
- The envelope uses `schema_version: 1`, stable `result_type: "HelpTopicResult"`, and a `data`
  payload containing `help_topic` and `text`.
- Topic matching is case-insensitive; output uses the canonical lowercase topic name and the exact
  text loaded from the existing packaged help topic.
- Only names returned by `available_help_topics()` are valid. An unknown topic emits one existing
  structured JSON error envelope with type `TabDatError`, a concise message, and exit status `1`.
- Retrieval occurs before config or `Executor` construction, reads no dataset, changes no session
  state, and materializes nothing. Existing terminal help, command execution, and JSON envelopes
  remain unchanged.
- `--help-topic` without `--json`, combined with `-c`, `-f`, a positional script, or
  `--list-commands`, and use in an interactive session are rejected clearly with existing CLI usage
  semantics.

## Examples

Valid:

```bash
uv run tabdat --json --help-topic summarize
```

Expected shape:

```json
{"data":{"help_topic":"summarize","text":"# summarize\n..."},"result_type":"HelpTopicResult","schema_version":1}
```

Unknown topic:

```bash
uv run tabdat --json --help-topic does-not-exist
```

Expected behavior: stderr retains `Error: unknown help topic: does-not-exist`, stdout contains one
structured error envelope, and the process exits with status `1`.

## Acceptance Criteria

- [x] One valid versioned success envelope contains the canonical topic and exact packaged help text.
- [x] Topic lookup is registry-derived, case-insensitive, and has no Executor/config/data/session side
  effects.
- [x] Unknown topics emit one stable structured JSON error envelope with exit status `1`.
- [x] Incompatible invocation combinations fail clearly without contaminating JSON output or changing
  existing success/error behavior.
- [x] Terminal help, command execution, interactive behavior, and existing JSON schemas remain
  unchanged.
- [x] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Command execution, script or multi-topic retrieval, option/argument schemas, catalog examples,
  plugin discovery, interactive JSON mode, dry-run/explain, repair diagnostics, operation lineage,
  new syntax, new help topics, or new exit codes.

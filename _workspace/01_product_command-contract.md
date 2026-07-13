# Product Contract: Phase 24 P1 — Structured JSON Command Schema Discovery

## Request Summary

Expose bounded machine-readable syntax and argument metadata for one discovered command without
executing it, creating a session, or reading data.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Invocation Rules

- `tabdat --json --describe-command summarize` emits exactly one compact deterministic
  `CommandSchemaResult` envelope.
- The data contains canonical `name`, `syntax`, `help_topic`, `arguments`, and `options` fields.
  Argument/option descriptors have stable names and bounded kind/required metadata; descriptor order
  is deterministic.
- Metadata is declarative registry data. It does not execute commands, invoke the full parser,
  inspect active data, resolve backend capabilities, estimate cost, or promise complete grammar
  validation.
- Unknown command names emit one existing structured JSON error envelope with type `TabDatError` and
  exit status `1`.
- Existing command execution, terminal output, interactive behavior, and JSON success/error envelopes
  remain unchanged. `--describe-command` is read-only and occurs before config/`Executor` setup.
- `--describe-command` without `--json`, combined with `-c`, scripts, other discovery flags,
  `--help-topic`, or `--explain`, and use in an interactive session are rejected clearly.

## Examples

Valid:

```bash
uv run tabdat --json --describe-command summarize
```

Expected shape:

```json
{"data":{"arguments":[{"name":"variables","required":false}],"help_topic":"summarize","name":"summarize","options":[],"syntax":"summarize [varlist]"},"result_type":"CommandSchemaResult","schema_version":1}
```

Unknown command:

```bash
uv run tabdat --json --describe-command does-not-exist
```

Expected behavior: stdout contains one existing structured error envelope, stderr retains the human
diagnostic, and the process exits with status `1`.

## Acceptance Criteria

- [ ] One known command emits one deterministic schema envelope with all five metadata fields.
- [ ] Argument/option descriptor names, required flags, and ordering are stable and bounded.
- [ ] Metadata lookup is pure and has no config/Executor/data/session side effects.
- [ ] Unknown commands emit one stable structured JSON error envelope with exit status `1`.
- [ ] Existing command execution, terminal output, interactive behavior, and JSON schemas remain
  unchanged.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Command execution, data-dependent planning, scripts, multiple-command output, plugin schemas,
  interactive JSON mode, effect estimates, full dry-run/explain behavior, repair diagnostics, new
  syntax, or new exit codes.

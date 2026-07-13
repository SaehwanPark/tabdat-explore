# Product Contract: Phase 24 P1 — Structured JSON Command Discovery

## Request Summary

Expose a stable read-only command catalog through the existing JSON interface without creating a
session or executing data commands.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Invocation Rules

- `tabdat --json --list-commands` emits exactly one compact deterministic success envelope.
- The envelope uses `schema_version: 1`, stable `result_type: "CommandCatalogResult"`, and a `data`
  payload containing `commands`.
- Each command entry has `name` and `help_topic`; `help_topic` is a string when a dedicated help
  topic exists and JSON `null` otherwise.
- Entries are sorted lexicographically by `name`, and names/help topics come from the existing command
  and help registries.
- The command does not instantiate an Executor, read a dataset, alter session state, or materialize
  anything. Terminal output and all existing JSON success/error envelopes remain unchanged.
- `--list-commands` without `--json`, combined with `-c`, `-f`, or a positional script, and use in an
  interactive session are rejected clearly with existing CLI usage semantics.

## Acceptance Criteria

- [ ] Catalog output is one valid versioned JSON envelope with complete stable command names and help
  availability.
- [ ] Catalog order is deterministic and registry-derived; no Executor/session side effects occur.
- [ ] Incompatible invocation combinations fail clearly without contaminating JSON output or changing
  existing error-envelope behavior.
- [ ] Terminal output, command execution, success/error schemas, and interactive behavior remain
  unchanged.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Command execution, plugin discovery, option/argument schemas, examples, interactive JSON mode,
  dry-run/explain, repair diagnostics, operation lineage, new syntax, or new exit codes.

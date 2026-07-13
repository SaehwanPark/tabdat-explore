# Product Contract: Phase 24 P1 — Structured JSON Declared Effect Categories

## Request Summary

Expose a finite, stable command-level effect vocabulary for machine clients without inspecting data,
estimating cost, planning resources, or executing commands.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Invocation Rules

- `tabdat --json --list-command-effects` emits exactly one deterministic versioned
  `CommandEffectCatalogResult` envelope with `data.commands` entries containing `name` and `effects`.
- Categories come from the finite vocabulary `read`, `write`, `control`, `plot`, and `unknown`.
- The canonical category order is exactly `read`, `write`, `control`, `plot`, `unknown`; every emitted
  tuple is non-empty, unique, and follows that order. `unknown` is emitted alone.
- A command may have multiple possible top-level effects, including active-dataset reads, output
  writes, artifact plots, and delegated `run`/`by` behavior. Categories do not inspect active data,
  account for options or predicates, estimate cost, plan resources, or imply execution.
- Existing command execution, terminal output, interactive behavior, and JSON success/error envelopes
  remain unchanged.
- `--list-command-effects` without `--json`, combined with command/script execution,
  `--list-commands`, `--help-topic`, or `--explain`, and use in an interactive session are rejected
  clearly.

## Examples

Expected catalog entries for the effect mapping:

```text
summarize -> [read]
generate  -> [read, write]
histogram -> [read, plot]
set       -> [control]
unknown   -> [unknown]
```

## Acceptance Criteria

- [x] The result uses one finite documented vocabulary and deterministic category ordering.
- [x] Every advertised command has an explicit mapping; unclassified commands report `unknown`.
- [x] Mapping is pure and does not inspect data, estimate cost, plan resources, or execute commands.
- [x] Existing command execution, terminal output, interactive behavior, and JSON schemas remain
  unchanged.
- [x] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Data-dependent effects, resource/state plans, estimates, command execution, scripts, option/argument
  schemas, catalog examples, plugin discovery, interactive JSON mode, full dry-run/explain behavior,
  repair diagnostics, operation lineage, new syntax, or new exit codes.

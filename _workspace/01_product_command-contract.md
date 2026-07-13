# Product Contract: Phase 24 P1 — Batch JSON Result Envelopes

## Request Summary

Expose a versioned JSON/JSONL result stream for non-interactive CLI execution without changing
command semantics or existing terminal output.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Roadmap Fit

This is the first narrow automation-output contract after the Phase 24 terminal semantics and
diagnostics slices. It establishes a stable success-result envelope while leaving discovery,
explainability, structured failures, and richer metadata to later slices.

## Existing Invocation

Valid forms add one CLI output flag:

- `tabdat --json -c "use data.parquet" -c "count"`
- `tabdat --json -f analysis.td`
- `tabdat --json analysis.td`

`--json` cannot be used with an interactive session. Existing invocations without `--json` retain
their terminal output byte-for-byte.

## Envelope Rules

- Every successful structured `Result` emits exactly one compact JSON object on stdout:

  ```json
  {"data":{...},"result_type":"CountResult","schema_version":1}
  ```

- Envelope keys are serialized deterministically. `schema_version` is the integer `1`; `result_type`
  is the stable public result label; `data` is the JSON-safe result payload.
- Multiple `-c` commands, scripts, and nested scripts emit one envelope per line in execution order.
  A command that returns no structured result emits no line.
- Missing values become JSON `null`; tuples become arrays; `Path` values become strings; exact
  `Decimal` values become lossless text rather than binary floating-point values; non-finite floats
  become JSON `null`.
- Script metadata, command dot-echoes, macro/directive notices, human tables, and plot auto-opening
  do not add stdout content in JSON mode.
- Parse and execution errors retain the existing stderr text and nonzero exit status. No structured
  error envelope is introduced in this slice.

## State And Compatibility Assumptions

- JSON serialization runs only after a successful Executor result is available, so it cannot mutate
  active data or alter validation atomicity.
- The output flag changes presentation only; parser grammar, Executor results, state transitions,
  materialization behavior, and terminal formatting remain unchanged.
- Interactive shell output remains terminal-only and does not accept `--json`.

## Acceptance Criteria

- [ ] `--json` emits deterministic single-command envelopes for representative load, status, table,
  preview, and transform results.
- [ ] Multiple commands and nested scripts produce clean JSONL in execution order without metadata or
  dot echoes, while commands returning no result emit no line.
- [ ] Missing values, paths, tuples, exact decimals, and non-finite floats follow the explicit JSON
  conversion policy.
- [ ] Terminal output remains unchanged and interactive `--json` misuse is rejected clearly.
- [ ] Parse/execution errors preserve stderr, exit status, and existing atomicity.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Interactive JSON mode, structured error envelopes, command discovery, dry-run/explain, repair
  diagnostics, SQL-result metadata, operation lineage, retained estimation samples, new syntax,
  new commands, new backends, or exit-code redesign.

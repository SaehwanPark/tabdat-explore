# Product Contract: Phase 24 P1 — Structured JSON Error Envelopes

## Request Summary

Add machine-readable failure envelopes to the existing batch/script JSONL output without changing
fail-fast execution, stderr diagnostics, terminal output, or exit status.

## Roadmap Phase

Phase 24 P1: Agent and automation interface.

## Roadmap Fit

This closes the first success/failure pair for the bounded JSON output interface. It does not add
recovery, new exit codes, command discovery, explainability, or repair behavior.

## Error Envelope Rules

- On the first parse or execution failure in `--json` `-c`/script execution, stdout emits exactly one
  compact deterministic object:

  ```json
  {"error":{"message":"...","type":"UnknownVariableError"},"schema_version":1}
  ```

- Script failures add `path` as a string and `line` as an integer inside `error`. Top-level `-c`
  failures have no source location.
- `type` uses an explicit stable label for the existing user-facing `TabDatError` hierarchy. The
  `message` is concise user-facing text; raw backend exception details and tracebacks are excluded.
- Successful result envelopes emitted before the failure remain in JSONL execution order. Execution
  remains fail-fast; no later command or script line runs.
- Existing human-readable stderr text and exit status `1` remain unchanged. Terminal mode and
  interactive mode remain unchanged.
- No error envelope is emitted in terminal mode. `--json` remains invalid for interactive sessions.

## State And Compatibility Assumptions

- Error serialization occurs only at the CLI boundary after Executor/parser failure; it does not
  change Executor state or validation atomicity.
- Nested script failures are emitted once by the outermost JSON batch boundary, retaining the original
  script path and line.
- Existing success-envelope schema version and payload policies remain unchanged.

## Acceptance Criteria

- [ ] Parse, execution, help-mode, and script failures emit one stable JSON error envelope with the
  expected message/type and script location when applicable.
- [ ] Prior success envelopes remain ordered, execution stops at the first failure, and no duplicate
  nested error envelope is emitted.
- [ ] Stderr, exit status `1`, terminal output, interactive behavior, and Executor atomicity remain
  unchanged.
- [ ] Error labels cover the existing user-facing error hierarchy exhaustively without tracebacks or
  raw backend details.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format, and integrated workflow checks pass.

## Non-Goals For This Slice

- Interactive JSON mode, error recovery, multi-error aggregation, new exit codes, SQL-result metadata,
  command discovery, dry-run/explain, repair diagnostics, operation lineage, new syntax, or new
  commands.

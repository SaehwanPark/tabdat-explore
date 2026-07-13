# Request Summary: Phase 24 P1 Batch JSON Result Envelopes

## Goal

Add a versioned machine-readable result envelope for non-interactive `-c` and script execution while
preserving existing command semantics, terminal formatting, and interactive behavior.

## Phase Fit

Phase 24 P1 Agent and automation interface. This is the first bounded output contract after the
completed terminal diagnostics slice; discovery, explainability, and structured errors remain later
contracts.

## Touched Surfaces

- `src/tabdat/cli.py`: `--json` batch/script routing, clean JSONL output, and mode validation
- `src/tabdat/formatter.py`: deterministic JSON envelope serialization alongside terminal formatting
- `src/tabdat/help/topics/run.md`, `docs/command-reference.md`, `docs/user-guide.md`:
  usage and output contract
- `tests/test_cli.py`, `tests/test_help.py`: single-command, multi-command, script, nested-script,
  serialization, error, and incompatible-mode coverage
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `--json` is a CLI output-mode flag valid only with `-c/--command`, `-f`, or a positional script;
  interactive sessions remain terminal-only.
- Each successful structured `Result` emits one compact JSON object line. Multiple commands and nested
  scripts form JSONL in execution order; commands returning no `Result` emit no line. `exit`/`quit`
  retain control behavior, while terminal-only `help` is rejected in JSON mode.
- Each envelope has `schema_version: 1`, a stable result-type label, and a `data` object containing
  the result payload. Missing values become JSON `null`, tuples become arrays, paths become strings,
  exact `Decimal` values remain lossless text, non-finite floats become JSON `null`, and bytes become
  `base64:<payload>` strings.
- Script metadata, command dot-echoes, macro/directive notices, and human tables are suppressed in
  JSON mode. Existing stderr errors and exit codes remain unchanged.
- Terminal output and all Executor state transitions are unchanged; JSON serialization occurs only
  after successful command execution.

## Non-Goals

- Interactive JSON mode, structured error envelopes, command discovery, dry-run/explain, repair
  diagnostics, SQL-result metadata, operation lineage, retained estimation samples, new commands,
  new backends, or exit-code redesign.

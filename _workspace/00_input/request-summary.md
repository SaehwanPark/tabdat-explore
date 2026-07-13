# Request Summary: Phase 24 P1 Structured JSON Syntax Preview

## Goal

Expose a syntax-only machine-readable preview for exactly one batch command without executing it,
creating a session, reading data, or changing terminal behavior.

## Phase Fit

Phase 24 P1 Agent and automation interface. This follows JSON success/error envelopes, command
discovery, and machine-readable help retrieval, and provides a deliberately narrow first step toward
dry-run/explain behavior before effect analysis or option schemas.

## Touched Surfaces

- `src/tabdat/models.py`: typed syntax-preview result model
- `src/tabdat/formatter.py`: terminal/JSON serialization and stable result-label coverage
- `src/tabdat/cli.py`: `--explain` validation, parser-only routing, and JSON error handling
- `docs/command-reference.md`, `docs/user-guide.md`, `src/tabdat/help/topics/run.md`: usage docs
- `tests/test_cli.py`, `tests/test_help.py`: success, parse error, state-free, and compatibility
  behavior
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `tabdat --json --explain -c <command>` is the only valid invocation for this slice; it emits one
  success envelope with `schema_version: 1`, stable `result_type`, `data.command_name`, and
  `data.execution: "not_run"`.
- `command_name` is the normalized leading command token (`?` maps to `help`, and `bayes:`/option
  punctuation is removed). No command execution, effect inference, AST class exposure, or data
  inspection is promised.
- Exactly one `-c/--command` is required. Syntax failures emit one existing structured JSON error
  envelope and exit status `1`; terminal stderr retains the existing parse message.
- Routing occurs before config or `Executor` construction and has no dataset or session side effects.
- Combining `--explain` with terminal mode, zero/multiple `-c`, `-f`, a positional script,
  `--list-commands`, `--help-topic`, or interactive mode fails clearly.
- Standard argparse `--help` retains conventional precedence and prints CLI usage without executing
  or previewing a command.

## Non-Goals

- Command execution, effect classification, estimates, state/resource plans, scripts, multiple
  commands, option/argument schemas, catalog examples, plugin discovery, interactive JSON mode, full
  dry-run/explain behavior, repair diagnostics, operation lineage, or new exit codes.

# Request Summary: Phase 24 P1 Structured JSON Command Discovery

## Goal

Add a read-only machine-readable command catalog to the existing JSON interface without changing
command execution, session state, terminal output, or success/error envelopes.

## Phase Fit

Phase 24 P1 Agent and automation interface. This follows the completed JSON success and failure
envelopes and provides a bounded discovery surface before option schemas, dry-run, and explain mode.

## Touched Surfaces

- `src/tabdat/models.py`: typed command-catalog entry/result models
- `src/tabdat/formatter.py`: terminal/JSON serialization and stable result-label coverage
- `src/tabdat/cli.py`: `--list-commands` validation and read-only catalog emission
- `src/tabdat/help/topics/run.md`, `docs/command-reference.md`, `docs/user-guide.md`: discovery usage
- `tests/test_cli.py`, `tests/test_help.py`: catalog content/order, incompatible modes, and state-free
  behavior
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `tabdat --json --list-commands` is the only invocation for this slice; it emits one success envelope
  with `schema_version: 1`, stable `result_type`, and `data.commands`.
- Each catalog entry contains a stable command `name` and `help_topic` string or JSON `null` when no
  dedicated topic exists. Entries are sorted lexicographically by command name.
- The catalog is derived from the existing command-name/help registries, does not instantiate an
  Executor, read data, or materialize a dataset, and has no side effects.
- Combining `--list-commands` with `-c`, `-f`, a positional script, or without `--json` fails clearly;
  interactive mode remains terminal-only.

## Non-Goals

- Command execution, plugin/extension discovery, option or argument schemas, examples, interactive
  JSON mode, dry-run/explain, repair diagnostics, operation lineage, or new exit codes.

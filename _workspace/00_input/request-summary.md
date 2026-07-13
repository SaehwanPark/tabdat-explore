# Request Summary: Phase 24 P1 Structured JSON Help-Topic Retrieval

## Goal

Expose one existing in-app help topic through the JSON interface without creating a session,
executing a command, reading data, or changing terminal behavior.

## Phase Fit

Phase 24 P1 Agent and automation interface. This follows the completed JSON success/error envelopes
and command discovery slice, giving machine clients access to the documented behavior behind a
discovered help topic before option schemas or dry-run/explain work.

## Touched Surfaces

- `src/tabdat/models.py`: typed help-topic result model
- `src/tabdat/formatter.py`: terminal/JSON serialization and stable result-label coverage
- `src/tabdat/cli.py`: `--help-topic` validation, lookup, and read-only JSON emission
- `docs/command-reference.md`, `docs/user-guide.md`, `src/tabdat/help/topics/run.md`: usage docs
- `tests/test_cli.py`, `tests/test_help.py`: success, unknown-topic, compatibility, and state-free
  behavior
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `tabdat --json --help-topic <topic>` is the only invocation for this slice; it emits one success
  envelope with `schema_version: 1`, stable `result_type`, and `data.help_topic`/`data.text`.
- Topic matching is case-insensitive and normalized to the existing lowercase help-topic name.
- Only topics returned by the existing `available_help_topics()` registry are valid. Unknown topics
  emit one existing structured JSON error envelope and exit status `1`.
- Retrieval happens before config or `Executor` construction and has no dataset or session side
  effects. Existing command execution, terminal help, and JSON success/error envelopes remain
  unchanged.
- Combining `--help-topic` with `-c`, `-f`, a positional script, `--list-commands`, or without
  `--json` fails clearly; interactive mode remains terminal-only.

## Non-Goals

- Command execution, script retrieval, multiple-topic output, option/argument schemas, examples,
  plugin discovery, interactive JSON mode, dry-run/explain, repair diagnostics, operation lineage,
  or new exit codes.

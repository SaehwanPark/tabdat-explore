# Request Summary: Phase 24 P1 Structured JSON Command Schema Discovery

## Goal

Expose bounded machine-readable syntax and argument metadata for one discovered command without
executing it, creating a session, reading data, or changing terminal behavior.

## Phase Fit

Phase 24 P1 Agent and automation interface. This follows JSON success/error envelopes, command/help
discovery, syntax preview, and declared effects, and provides a narrow option-schema surface before
full parser/execution planning.

## Touched Surfaces

- `src/tabdat/models.py`: typed command-schema metadata models
- `src/tabdat/formatter.py`: JSON serialization and stable result-label coverage
- `src/tabdat/cli.py`: `--describe-command` validation and read-only routing
- `src/tabdat/help/topics/`, `docs/command-reference.md`, `docs/user-guide.md`: metadata docs
- `tests/test_cli.py`, `tests/test_help.py`: known/unknown command, ordering, and side-effect coverage
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `tabdat --json --describe-command <name>` emits one versioned result for one known command with a
  canonical name, syntax string, help-topic availability, and bounded argument/option descriptors.
- Metadata is declarative and registry-derived. It does not execute a parser branch, inspect data,
  resolve backend capabilities, estimate cost, or promise complete grammar validation.
- Unknown command names emit one existing structured JSON error envelope and exit status `1`.
- The path is batch-only and cannot be combined with command/script execution, other discovery flags,
  explain/help-topic flags, or interactive mode.

## Non-Goals

- Command execution, data-dependent planning, scripts, multiple-command output, plugin schemas,
  interactive JSON mode, effect estimates, full dry-run/explain, repair diagnostics, operation
  lineage, new syntax, or new exit codes.

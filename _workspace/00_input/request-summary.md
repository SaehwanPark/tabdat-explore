# Request Summary: Phase 24 P1 Structured JSON Error Envelopes

## Goal

Extend the existing non-interactive `--json` result stream with versioned error envelopes while
preserving fail-fast execution, human-readable stderr, terminal output, and current exit status.

## Phase Fit

Phase 24 P1 Agent and automation interface. This follows the completed JSON success-envelope slice
and closes the first machine-readable failure boundary before discovery, explainability, and repair
diagnostics.

## Touched Surfaces

- `src/tabdat/cli.py`: JSON error emission at command and script boundaries without duplicate output
- `src/tabdat/formatter.py`: stable error labels and JSON-safe error envelopes
- `src/tabdat/errors.py`, `src/tabdat/script.py`: existing error hierarchy/location fields only if
  needed for explicit serialization
- `src/tabdat/help/topics/run.md`, `docs/command-reference.md`, `docs/user-guide.md`: failure-mode
  documentation
- `tests/test_cli.py`, `tests/test_help.py`: parse, execution, help, script-location, ordering, and
  terminal-compatibility coverage
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- JSON success envelopes remain unchanged: `schema_version: 1`, stable `result_type`, and `data`.
- On the first parse or execution failure in a JSON batch/script run, stdout emits exactly one error
  envelope with `schema_version: 1` and an `error` object containing stable `type` and `message`;
  script failures also include string `path` and integer `line`.
- Successful envelopes emitted before the failure remain in execution order; later commands do not
  run. A top-level `-c` failure has no source location.
- Existing human-readable stderr text and exit status `1` remain unchanged. No traceback or raw
  backend exception details are emitted.
- Terminal mode and interactive mode remain unchanged; `--json` remains batch/script-only.

## Non-Goals

- Interactive JSON mode, error recovery, multi-error aggregation, new exit codes, structured SQL
  metadata, command discovery, dry-run/explain, repair diagnostics, operation lineage, or new commands.

# Request Summary: Phase 24 P1 Structured JSON Declared Effect Categories

## Goal

Expose a finite, stable command-level effect vocabulary for machine clients without inspecting data,
estimating cost, planning resources, or executing commands.

## Phase Fit

Phase 24 P1 Agent and automation interface. This follows JSON success/error envelopes, command/help
discovery, and parser-only syntax preview, and is a bounded step toward full dry-run/explain behavior.

## Touched Surfaces

- `src/tabdat/models.py`: typed effect-category result model
- `src/tabdat/formatter.py`: terminal/JSON serialization and stable result-label coverage
- `src/tabdat/cli.py`: `--list-command-effects` routing and read-only emission
- `docs/command-reference.md`, `docs/user-guide.md`, `src/tabdat/help/topics/run.md`: semantics/docs
- `tests/test_cli.py`, `tests/test_help.py`: vocabulary, mapping, unknown, and compatibility coverage
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `tabdat --json --list-command-effects` emits one deterministic catalog envelope whose entries map
  each advertised command to one or more declared effect categories; existing command execution and
  JSON success/error envelopes remain unchanged.
- Categories are command-level declarations only. They do not inspect an active dataset, account for
  options or predicates, estimate cost, or imply a full execution plan.
- Every advertised command has an explicit category mapping; any future/unclassified command uses
  `unknown` rather than an inferred category.
- Terminal and interactive behavior remain unchanged; the new machine-readable path is batch-only.

## Non-Goals

- Data-dependent planning, resource/state plans, estimates, command execution, scripts, option/
  argument schemas, catalog examples, plugin discovery, interactive JSON mode, full dry-run/explain,
  repair diagnostics, operation lineage, or new exit codes.

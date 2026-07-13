# QA Report: Phase 24 P1 Structured JSON Syntax Preview

Status: implementation validation complete; PR review pending

## Boundaries Checked

- **Preview contract:** `--json --explain -c <command>` emits exactly one versioned
  `CommandExplainResult` with the parsed command type and `execution: "not_run"`.
- **Parser failure:** invalid syntax emits one existing `ParseError` JSON envelope, retains human
  stderr, and exits `1`.
- **Read-only behavior:** preview runs before config/`Executor` setup and does not read data,
  materialize a relation, or alter session state.
- **Invocation safety:** missing JSON, zero/multiple `-c`, scripts, positional paths, discovery,
  help-topic retrieval, and interactive mode fail clearly without JSON stdout contamination.
- **Compatibility:** existing command execution, terminal output, interactive behavior, and JSON
  success/error envelopes remain unchanged.

## Blocking Issues

- None remain from implementation validation.

## Validation Evidence

- Focused JSON/catalog/help-topic/explain CLI checks: 43 passed.
- Focused help/docs checks: 2 passed.
- `uv run pytest -q` — 1,185 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract
  s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood
  s6_canonical_parquet_workflow` — exit 0; all six integrated scenarios passed, including canonical
  replay with matching stdout.

## PR Review Loop

No independent PR review passes have started yet. The required loop is exactly three reviews after
the PR is opened; findings will be fixed and validated without starting a fourth review.

## Non-Blocking Follow-Ups

Effect classification, estimates, state/resource plans, scripts, multiple commands, option/argument
schemas, catalog examples, plugin discovery, interactive JSON mode, full dry-run/explain, repair
diagnostics, SQL-result metadata, operation lineage, retained estimation samples, differential
assurance, dependency layering, and preview readiness remain queued in `SPEC.md` Future.

## Recommended Next Action

Commit and push the implementation, open the PR, then run exactly three independent review passes.

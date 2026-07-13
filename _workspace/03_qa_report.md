# QA Report: Phase 24 P1 Structured JSON Syntax Preview

Status: implementation validation complete; exactly three independent PR reviews complete

## Boundaries Checked

- **Preview contract:** `--json --explain -c <command>` emits exactly one versioned
  `CommandExplainResult` with a stable normalized `command_name` and `execution: "not_run"`.
- **Parser failure:** invalid or empty syntax emits one existing `ParseError` JSON envelope, retains
  human stderr, and exits `1`.
- **Read-only behavior:** preview runs before config/`Executor` setup and does not read data,
  materialize a relation, or alter session state, including explicit invalid config paths.
- **Stable naming:** built-ins, conditional forms, and `run` previews use normalized command names;
  Python parser class names are not exposed as schema values.
- **Invocation safety:** missing JSON, zero/multiple `-c`, scripts, positional paths, discovery,
  help-topic retrieval, and interactive mode fail clearly; standard `--help` retains argparse
  precedence without previewing.
- **Compatibility:** existing command execution, terminal output, interactive behavior, and JSON
  success/error envelopes remain unchanged.

## Blocking Issues

- None remain.

## Validation Evidence

- Focused JSON/catalog/help-topic/explain CLI checks: 49 passed.
- Focused help/docs checks: 2 passed.
- `uv run pytest -q` — 1,191 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract
  s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood
  s6_canonical_parquet_workflow` — exit 0; all six integrated scenarios passed, including canonical
  replay with matching stdout.

## PR Review Loop

Exactly three independent reviews completed. Review 1 found conventional `--help` precedence; Review 2
found unstable Python AST-type labels; Review 3 found stale handoff wording and missing edge-case
regressions. The behavior/documentation and tests were updated, and the complete validation set was
rerun. No fourth review was started.

## Non-Blocking Follow-Ups

Effect classification, estimates, state/resource plans, scripts, multiple commands, option/argument
schemas, catalog examples, plugin discovery, interactive JSON mode, full dry-run/explain, repair
diagnostics, SQL-result metadata, operation lineage, retained estimation samples, differential
assurance, dependency layering, and preview readiness remain queued in `SPEC.md` Future.

## Recommended Next Action

Merge the reviewed PR, then remove the local and remote feature branch and return to `SPEC.md` for the
next bounded slice.

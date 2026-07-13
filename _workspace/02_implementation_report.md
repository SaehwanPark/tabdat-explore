# Implementation Report: Phase 24 P1 Structured JSON Syntax Preview

## Contract Consumed

- `_workspace/01_product_command-contract.md` — a parser-only JSON preview for exactly one batch
  command, with `not_run` execution and existing structured parse errors.

## Delivered Boundary

- `src/tabdat/models.py`
  - Added strict typed `CommandExplainResult` and included it in the public `Result` union.
- `src/tabdat/formatter.py`
  - Added the stable `CommandExplainResult` label to the exhaustive result-label map and a total
    terminal formatter branch.
- `src/tabdat/cli.py`
  - Added `--explain`, requiring exactly one `-c/--command` and `--json`.
  - Parses one command before config or `Executor` construction and emits its stable dataclass type
    with `execution: "not_run"`.
  - Routes parser failures through the existing JSON error envelope while preserving human stderr.
- Help/docs/tests
  - Documented syntax-only preview limits in the command reference, user guide, and `run` help.
  - Added success, parser-error, no-session, exact-cardinality, and incompatible-invocation coverage
    while preserving existing terminal and JSON behavior.

## Functional-First Notes

The preview is a pure parser/presentation boundary. It deliberately makes no claims about effects,
resource plans, estimates, state transitions, or execution equivalence, and it never instantiates an
`Executor` or loads config/data.

## Validation Commands And Outcomes

- `uv run pytest tests/test_cli.py -k 'json or list_commands or help_topic or explain' -q` — passed,
  43 tests.
- `uv run pytest tests/test_help.py -k 'run_help or current_commands' -q` — passed, 2 tests.
- `uv run pytest -q` — passed, 1,185 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 35 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract
  s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood
  s6_canonical_parquet_workflow` — passed with exit code 0; all six scenarios passed and canonical
  replay stdout matched.
- PR review loop: pending; no review passes have been started for this slice.

## Known Limits And Follow-Up Work

Effect classification, estimates, state/resource plans, scripts, multiple commands, option/argument
schemas, plugin discovery, interactive JSON mode, full dry-run/explain, repair diagnostics, lineage,
new exits, and new syntax remain separate Phase 24 contracts. The implementation is ready for PR
review.

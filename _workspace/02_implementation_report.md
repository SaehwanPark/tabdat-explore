# Implementation Report: Phase 24 P1 Structured JSON Help-Topic Retrieval

## Contract Consumed

- `_workspace/01_product_command-contract.md` — one read-only JSON envelope for an existing
  case-insensitive help topic, with structured unknown-topic failures and no session setup.

## Delivered Boundary

- `src/tabdat/models.py`
  - Added strict typed `HelpTopicResult` and included it in the public `Result` union.
- `src/tabdat/formatter.py`
  - Added the stable `HelpTopicResult` label to the exhaustive result-label map and a total terminal
    formatter branch.
- `src/tabdat/cli.py`
  - Added `--help-topic TOPIC`, requiring `--json` and rejecting command/script/discovery mixes.
  - Performs normalized registry lookup and packaged help loading before config or `Executor`
    construction.
  - Emits one success envelope or the existing structured error envelope for an unknown topic.
- Help/docs/tests
  - Documented machine-readable help retrieval in the command reference, user guide, and `run` help.
  - Added case normalization, exact text, unknown-topic, no-session, and incompatible-invocation
    coverage while preserving existing terminal and JSON behavior.

## Functional-First Notes

Help-topic retrieval is a pure read-only boundary over packaged resources and the existing help
registry. It does not instantiate an `Executor`, load config, access datasets, materialize relations,
alter session state, or change command execution.

## Validation Commands And Outcomes

- `uv run pytest tests/test_cli.py -k 'json or list_commands or help_topic' -q` — passed, 32 tests.
- `uv run pytest tests/test_help.py -k 'run_help or current_commands' -q` — passed, 2 tests.
- `uv run pytest -q` — passed, 1,173 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract
  s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood
  s6_canonical_parquet_workflow` — passed with exit code 0; all six scenarios passed and canonical
  replay stdout matched.
- PR review loop: pending; no review passes have been started for this slice.

## Known Limits And Follow-Up Work

Multiple-topic retrieval, option/argument schemas, catalog examples, plugin discovery, interactive
JSON mode, dry-run/explain, repair diagnostics, SQL-result metadata, operation lineage, estimation
samples, new exit codes, and new help topics remain separate Phase 24 contracts. The implementation
is ready for PR review.

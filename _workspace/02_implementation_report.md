# Implementation Report: Phase 24 P1 Structured JSON Error Envelopes

## Contract Consumed

- `_workspace/01_product_command-contract.md` — one versioned JSON error envelope at the first
  non-interactive parse/execution failure, with stable type/message and script location.

## Delivered Boundary

- `src/tabdat/formatter.py`
  - Added an explicit exhaustive `ERROR_TYPE_LABELS` map for the user-facing error hierarchy.
  - Added deterministic error envelopes with concise sanitized messages and optional script path/line
    fields; raw causes remain available only in human stderr.
- `src/tabdat/cli.py` and `src/tabdat/script.py`
  - Emits one JSON error envelope at top-level command and script boundaries while preserving prior
    success envelopes, fail-fast execution, human stderr, and exit status `1`.
  - Nested failures use resolved paths; invalid UTF-8 scripts report a source line derived from newline
    positions rather than a byte offset.
- Help/docs/tests
  - Documented machine-readable failure behavior in run help, command reference, and user guide.
  - Added parse, execution, help, script-location, nested-script, invalid-UTF8, raw-cause sanitization,
    fail-fast, hierarchy-label, and terminal-compatibility coverage.

## Functional-First Notes

Error serialization is a pure CLI presentation step after parser/Executor failure. It does not alter
the existing error hierarchy, Executor state, rollback behavior, or command control flow.

## Validation Commands And Outcomes

- `uv run pytest tests/test_cli.py -k 'json' -q` — passed, 19 tests.
- `uv run pytest tests/test_help.py -k 'run_help' -q` — passed, 1 test.
- `uv run pytest -q` — passed, 1,161 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood s6_canonical_parquet_workflow` — passed with exit code 0; all scenarios passed and canonical replay stdout matched.
- Exactly three independent PR reviews completed; all findings were fixed, and no fourth review was
  started.

## Known Limits And Follow-Up Work

Interactive JSON mode, error recovery, multi-error aggregation, new exit codes, command discovery,
dry-run/explain, repair diagnostics, SQL-result metadata, operation lineage, and retained estimation
samples remain separate Phase 24 contracts. The reviewed implementation is ready for PR update and
merge.

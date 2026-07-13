# Implementation Report: Phase 24 P1 Structured JSON Command Discovery

## Contract Consumed

- `_workspace/01_product_command-contract.md` — one deterministic JSON command catalog derived from
  the existing command and help registries without starting a session or executing data commands.

## Delivered Boundary

- `src/tabdat/models.py`
  - Added strict typed `CommandCatalogEntry` and `CommandCatalogResult` models.
  - Added `CommandCatalogResult` to the public `Result` union.
- `src/tabdat/formatter.py`
  - Added the stable `CommandCatalogResult` label to the exhaustive JSON result-label map.
  - Added a total terminal formatter branch for the typed result.
- `src/tabdat/cli.py`
  - Added `--list-commands`, requiring `--json` and rejecting command/script execution arguments.
  - Emits one compact catalog envelope before config or `Executor` construction.
  - Sorts the existing `COMMAND_NAMES` registry and maps each name to its available help topic or
    JSON `null`.
- `src/tabdat/shell.py`
  - Kept the executable command registry complete for the catalog by adding `lincom`, `test`, and
    `ttest`, which have no dedicated help topics and therefore report `null`.
- Help/docs/tests
  - Documented discovery in the command reference, user guide, and `run` help topic.
  - Added catalog ordering/help availability, no-session construction, and incompatible-invocation
    coverage, including explicit assertions for the three previously omitted executable commands,
    while preserving existing JSON and terminal tests.

## Functional-First Notes

Catalog construction is a pure read-only presentation path over existing registries. It does not
instantiate an `Executor`, load config, read a dataset, materialize a relation, alter session state,
or change command execution and existing success/error envelopes.

## Validation Commands And Outcomes

- `uv run pytest tests/test_cli.py -k 'json or list_commands' -q` — passed, 24 tests.
- `uv run pytest tests/test_help.py -k 'run_help or current_commands' -q` — passed, 2 tests.
- `uv run pytest -q` — passed, 1,166 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py s1_titanic_batch_core s2_interactive_shell_contract
  s3_taxi_lazy_scale s4_penguins_script_repro s5_titanic_phase13_dogfood
  s6_canonical_parquet_workflow` — passed with exit code 0; all six scenarios passed and canonical
  replay stdout matched.
- Exactly three independent PR reviews completed: two reviewers identified the same incomplete
  registry issue and one reported no findings. The registry/test fix and stale handoff wording were
  applied; no fourth review was started.

## Known Limits And Follow-Up Work

Option/argument schemas, command examples in the catalog, plugin discovery, interactive JSON mode,
dry-run/explain, repair diagnostics, SQL-result metadata, operation lineage, estimation samples,
new exit codes, and new commands remain separate Phase 24 contracts. The implementation is ready for
PR merge.

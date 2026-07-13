# Implementation Report: Phase 24 P0 Materialization Reason Transparency

## Contract Consumed

- `_workspace/01_product_command-contract.md` — `status` materialization-reason extension.

## Delivered Boundary

- `src/tabdat/executor.py`
  - Added typed session metadata for the last successful tracked Polars fallback.
  - Uses a small public-execution commit boundary so `polars_fallback` is recorded only after the
    requested command succeeds, even though the fallback hook runs before command dispatch.
  - Resets the reason after a successful source load or named-table activation.
  - Resets the reason after successful `sql ... into <table>` activation.
  - Keeps unsupported `ByCommand` validation before the lazy materialization hook.
- `src/tabdat/models.py` and `src/tabdat/formatter.py`
  - Added the optional typed reason to `StatusResult`.
  - Render `Last materialization reason: polars fallback|none` in the contracted position.
- `tests/`
  - Covers initial/eager/DuckDB-lazy/Polars-lazy `none` states, successful fallback, failed
    unsupported `by` preservation, source/table reset, exact no-active output, `-c` and script
    flows, parser, shell completion, and help.
- `src/tabdat/help/topics/status.md`, `docs/command-reference.md`, `docs/user-guide.md`,
  `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Documented the narrow fallback taxonomy, examples, non-goals, and verification evidence.

## Implementation Notes By Boundary

- State: the reason is session metadata for the last successful tracked Polars fallback, not full
  operation lineage.
- Lazy boundary: status remains dispatched before the materialization hook; the hook stages the
  reason after collecting the lazy frame, and the executor commits it only after command success.
- Reset boundary: successful `use`, named-table activation, and `sql ... into <table>` clear the
  reason; failed operations do not claim a fallback.
- Output: the internal typed value `polars_fallback` is normalized to the public phrase
  `polars fallback`; no backend inspection is added to formatting.
- Scope: reasons for other DuckDB/eager materialization paths remain intentionally unmodeled.

## Validation Commands And Outcomes

- `uv run pytest tests/test_executor.py -k 'status or fallback' -q` — passed, 8 tests.
- `uv run pytest tests/test_cli.py -k 'phase_24_status or fallback_reason' -q` — passed, 5 tests.
- `uv run pytest tests/test_parser.py -k 'status or by' -q` — passed, 8 tests.
- `uv run pytest tests/test_shell.py -k 'command_names or by' -q` — passed, 3 tests.
- `uv run pytest tests/test_help.py -k help_topics -q` — passed, 2 tests.
- `uv run pytest` — passed, 962 tests, with 314 existing third-party warnings.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — passed; all six scenarios passed, including
  canonical replay with exact stdout/table equivalence and 4.362 seconds composite duration.

## Known Limits And Follow-Up Work

- The reason taxonomy currently covers only the existing Polars lazy-to-eager fallback hook.
- Full operation lineage, active-operation reporting, broader materialization causes, retained
  estimation samples, machine-readable output, and explain/dry-run remain future Phase 24 work.

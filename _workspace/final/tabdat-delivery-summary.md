# Delivery Summary: Silent Plot Drawing & Clickable File Links

## Delivered Capabilities
1. **Silent Plot Drawing by Default**:
   - `TabDatConfig.graph_open` now defaults to `False` (`off`).
   - Plot generation commands (`histogram`, `scatter`, `bar`, `bayesplot`, `estat report`) save files silently in the background without automatically popping open external applications or browsers.
   - Users can still optionally enable auto-open per session via `set graph_open on` or in config via `graph_open = true`.

2. **Clickable `file://<path>` URIs**:
   - `format_result(PlotResult(...))` formats plot output with full RFC 8089 `file://` URIs (e.g. `Saved plot: file:///Users/.../artifacts/plots/histogram-age.svg`), enabling instant terminal click-to-open.

3. **Guaranteed Test Suite Isolation**:
   - `tests/conftest.py` adds an `autouse=True` fixture `prevent_opening_browser` mocking `tabdat.cli._open_path` so no test ever launches a browser or external viewer process.

## Changed Files
- `src/tabdat/config.py`: `graph_open = False` default in `TabDatConfig`.
- `src/tabdat/formatter.py`: `_plot_uri` helper and `file://` formatting for `PlotResult`.
- `tests/conftest.py`: Autouse fixture preventing browser/viewer process launches.
- `tests/test_config.py`: Default config assertions.
- `tests/test_cli.py`: Updated CLI plot assertions and config banners.
- `integrated_testing/run_e2e.py`: Updated E2E scenarios for plot URI outputs.
- `docs/user-guide.md` & `ARCHITECTURE.md`: Updated documentation.

## Validation Commands
- `uv run pytest` -> 1,223 passed
- `uv run python integrated_testing/run_e2e.py` -> All 6 scenarios passed
- `uv run basedpyright` -> 0 errors, 0 warnings, 0 notes
- `uv run python scripts/check_docs_alignment.py` -> PASSED
- `uv run ruff check . && uv run ruff format --check .` -> PASSED

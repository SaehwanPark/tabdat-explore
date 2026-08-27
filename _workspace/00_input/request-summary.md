# Request Summary: `doctor` Command & Environment Diagnostics

## Goal
Implement `tabdat doctor` and the interactive `doctor` command to inspect, verify, and report the operational health and capability status of the TabDat environment:
1. Core capabilities: DuckDB, PyArrow, Polars, Plotting engines (Altair/Matplotlib).
2. Conventional statistics capabilities: statsmodels, linearmodels, scipy.
3. Optional/specialized capabilities: ML (scikit-learn), Bayesian (bambi/PyMC), Spatial (spreg/libpysal), R integration (rpy2 / R runtime).
4. System metadata: Python version, OS platform, architecture.
5. Provide clean terminal diagnostics table, actionable missing-capability guidance, and structured JSON output.
6. Support top-level `tabdat doctor` and `tabdat --json doctor` CLI invocation, as well as interactive `doctor` command in session/scripts.

## Phase Fit
Phase 17 & Phase 24B (`docs/tabdat_forward_roadmap.md` Sections 6, 17, 21).

## Touched Surfaces
- `src/tabdat/models.py`: `DoctorCommand`, `DoctorCapabilityItem`, `DoctorResult`.
- `src/tabdat/parser.py`: `doctor` grammar, catalog entries, command effect registration.
- `src/tabdat/doctor.py`: Diagnostics inspection logic, safe dependency inspection without unhandled exceptions.
- `src/tabdat/executor.py`: Handler for `DoctorCommand`.
- `src/tabdat/formatter.py`: Text formatting for `DoctorResult` and JSON envelope support.
- `src/tabdat/cli.py`: Top-level `tabdat doctor` CLI handling, catalog schemas.
- `src/tabdat/help/topics/doctor.md` & `src/tabdat/help/__init__.py`: In-app help topic.
- `docs/command-reference.md`, `docs/user-guide.md`, `README.md`: Documentation updates.
- Tests: `tests/test_doctor.py`, `tests/test_cli.py`, `tests/test_parser.py`.

## Assumptions
- `doctor` is a read-only introspection command (effect: `metadata`).
- Safe introspection must gracefully detect missing optional packages without throwing uncaught import errors.
- Both human-readable terminal output and structured `--json` output derive from the same `DoctorResult` model.

## Non-Goals
- Attempting automatic installation of missing system binaries (e.g. system R compiler).
- Materializing or modifying the active dataset.

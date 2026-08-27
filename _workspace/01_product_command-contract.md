# Product Contract: Fast Startup Optimization & v0.24.0 Release

## Request Summary
Drastically reduce CLI startup latency through lazy deferred imports and fast CLI routing while preserving 100% semantic and test compatibility.

## Invariants & Optimization Specifications

### 1. Lazy Statistical Imports (`src/tabdat/executor.py`)
- Core modules (`tabdat.models`, `tabdat.parser`, `tabdat.backend`, `tabdat.formatter`, `tabdat.shell`) must not import `statsmodels`, `libpysal`, `spreg`, `linearmodels`, `scikit-learn`, or `scipy.optimize` at module load time.
- Heavy statistical libraries are imported inside their respective command execution methods (e.g. `_execute_regress`, `_execute_spregress`, `_execute_ivregress`, `_execute_lasso`, etc.).
- When an optional library is missing or fails to import, the existing actionable error behavior is preserved.

### 2. Lazy Visualization Imports (`src/tabdat/visualization.py`)
- `altair`, `matplotlib`, and `vl_convert` are imported on demand when executing `scatter`, `histogram`, or `bar`.

### 3. Fast CLI Dispatch (`src/tabdat/cli.py`)
- When invoked with `--version`, `--help`, or `doctor`, the CLI routes immediately without allocating database sessions or compiling execution graph primitives unnecessarily.

### 4. Release & Version Bump
- Package version bumped to `0.24.0` in `pyproject.toml` and Homebrew formula.
- Release workflow on tag `v0.24.0` builds and publishes distribution assets.

## Acceptance Criteria
- [ ] Startup latency measured via `python -X importtime -c "import tabdat.cli"` decreases by $\ge 80\%$ (from ~1,820ms to $\le 300$ms).
- [ ] All 1,249 existing tests pass without regressions.
- [ ] `basedpyright`, `ruff`, and `scripts/check_docs_alignment.py` pass cleanly.
- [ ] PR created and merged into `main`.
- [ ] Release tag `v0.24.0` created on GitHub.

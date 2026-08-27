# Request Summary: Fast Startup Optimization & v0.24.0 Release

## Goal
1. Implement Strategy 1 (Lazy statistical imports in `src/tabdat/executor.py`), Strategy 2 (Lazy visualization imports in `src/tabdat/visualization.py`), and Strategy 3 (Fast CLI dispatch for `--help`, `--version`, and `doctor`).
2. Optimize cold startup latency from ~1.82s down to < 0.25s (~8x-9x faster).
3. Bump package version to `0.24.0`.
4. Open PR, merge into `main`, and create GitHub release tag `v0.24.0` triggering automated release asset publishing.

## Touched Surfaces
- `src/tabdat/executor.py`: Defer heavy imports (`statsmodels`, `spreg`, `libpysal`, `linearmodels`, `scikit-learn`, `scipy.optimize`, etc.) to specific command execution methods.
- `src/tabdat/visualization.py`: Defer `altair` and `matplotlib` to `render_chart()`.
- `src/tabdat/cli.py`: Fast path for `--version`, `--help`, and `doctor` before full executor initialization.
- `pyproject.toml`, `Formula/tabdat.rb`: Bump version to `0.24.0`.

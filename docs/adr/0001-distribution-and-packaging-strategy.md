# ADR 0001: Distribution and Packaging Strategy

- **Status**: Accepted
- **Date**: 2026-08-27
- **Deciders**: Product Architecture & Tooling Team
- **Consulted**: `docs/tabdat_forward_roadmap.md` (Phases 25, 28, 29, 30, 31)

---

## Context

TabDat-Explore is a terminal-native exploratory data analysis and econometrics tool. For routine research workflows, analysts and data scientists need to run `tabdat` globally from any project directory without cloning repositories or manually activating project virtual environments.

We evaluated multiple distribution options to balance:
1. **Frictionless Installation**: One command for macOS and Linux users.
2. **Startup Performance**: Minimal cold and warm startup latency.
3. **Payload Footprint**: Avoiding multi-gigabyte monolithic bundles.
4. **Reliability & Maintenance**: Seamless C-extension compatibility (DuckDB, PyArrow, Polars) and clean diagnostic reporting.

---

## Candidates Evaluated

| Candidate | Mechanism | Cold Startup | Artifact Size | Maintenance Burden | Compatibility / Notes |
|-----------|-----------|--------------|---------------|-------------------|-----------------------|
| **`uv tool` / Shell Installer** | Isolated virtual tool managed by Astral `uv` | ~0.15s - 0.25s | ~80 MB virtualenv | Minimal (pure PyPI/git wheels) | **Recommended**. Fast, reliable, automatic binary wheels for DuckDB/PyArrow. |
| **Homebrew Formula** | `brew install SaehwanPark/tabdat/tabdat` | ~0.20s - 0.30s | System-managed `libexec` | Low (automated formula updates) | **Recommended for macOS/Linux brew users**. Native OS integration. |
| **PyInstaller `onedir`** | Frozen directory bundle with bundled CPython runtime | ~0.35s - 0.50s | ~250-400 MB | Moderate (hook maintenance for PyArrow/DuckDB) | Good fallback for environments without Python or `uv`. |
| **PyInstaller `onefile`** | Single self-extracting executable | ~1.50s - 3.00s | ~180-250 MB | Moderate (slow startup due to `/tmp` unpacking) | Rejected for interactive CLI due to extraction latency. |
| **Nuitka Standalone** | C-transpiled Python compilation | ~0.20s - 0.40s | ~200-350 MB | High (complex build matrix and C-extension hooks) | Deferred until native binary distribution is strictly required. |

---

## Decision

1. **Primary Distribution Channels (Tier 1)**:
   - **One-Command Shell Installer**: `curl -LsSf https://raw.githubusercontent.com/SaehwanPark/tabdat-explore/main/scripts/install.sh | sh` (bootstraps `uv` and installs TabDat as a global tool).
   - **`uv tool` Direct Install**: `uv tool install tabdat-explore` / `uv tool install git+https://github.com/SaehwanPark/tabdat-explore.git`.
   - **Homebrew Tap**: `brew install SaehwanPark/tabdat/tabdat` using [`Formula/tabdat.rb`](../../Formula/tabdat.rb).

2. **Capability Gating & Packaging Boundaries**:
   - The core package bundles modern tabular engines (DuckDB, PyArrow, Polars) and standard econometrics (`statsmodels`, `scipy`).
   - Heavy optional ecosystems (such as external R runtime via `rpy2`, full Bayesian MCMC with Bambi/PyMC, and spatial packages) are discovered safely at runtime without crashing imports.
   - The `tabdat doctor` diagnostic command provides transparent capability inspection and remediation steps.

3. **Standalone Binary Freezing (Tier 2)**:
   - Evaluated as secondary; PyInstaller `onedir` builds will be produced if zero-Python enterprise container environments require it. Single-file self-extracting binaries (`onefile`) are rejected due to unacceptably high startup latency on interactive prompts.

---

## Consequences

- **Positive**: Users gain instant global access to `tabdat` in < 5 seconds via `curl | sh` or `brew install`.
- **Positive**: Startup latency remains fast (~150ms).
- **Positive**: No brittle C-transpilation hooks or runtime unpacking overhead.
- **Negative**: Users without `uv` or Python rely on the installer script to bootstrap `uv` into `~/.local/bin`.

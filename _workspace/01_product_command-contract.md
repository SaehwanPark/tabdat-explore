# Product Contract: `doctor` Command & Environment Diagnostics

## Request Summary
Add `tabdat doctor` CLI subcommand and interactive `doctor` command to inspect capability health across core, statistics, optional, and system layers.

## Roadmap Phase
Phase 17 (`tabdat doctor`) & Phase 24B (Capability Boundaries).

## Syntax
```stata
doctor
```

CLI:
```bash
tabdat doctor
tabdat --json doctor
```

## Invocation & Semantics Rules

### 1. Interactive & Script Semantics
- Command: `doctor`
- Arguments/Options: `doctor` takes no arguments, if-clauses, or options. Passing arguments or options raises `ParseError`.
- State Effects: Pure introspection / metadata. Does not mutate dataset, active table, or estimation state.
- Output: Returns `DoctorResult` containing structured capability groups: `core`, `statistics`, `optional`, and `system`.

### 2. Capabilities Inspected
- **Core Layer**:
  - `DuckDB`: DuckDB SQL engine status & version.
  - `PyArrow`: Apache Arrow table / Parquet IO status & version.
  - `Polars`: Polars lazy engine status & version.
  - `Plotting`: Altair / Matplotlib chart rendering status & versions.
- **Statistics Layer**:
  - `statsmodels`: Econometric & linear model engine & version.
  - `linearmodels`: Panel / IV estimation engine & version.
  - `scipy`: Numerical optimization & statistical distribution substrate & version.
- **Optional Layer**:
  - `ML`: `scikit-learn` regularized & ML models status & version.
  - `Bayesian`: `bambi` / `pymc` MCMC backend status & version.
  - `Spatial`: `spreg` & `libpysal` spatial econometrics backend status & versions.
  - `R`: `rpy2` bridge and underlying R runtime/packages status.
- **System Layer**:
  - Python version, Platform/OS, Machine architecture, Executable path.

### 3. CLI Subcommand
- Invoking `tabdat doctor` directly prints the diagnostic report and exits with 0 (or 1 if critical core engine is broken).
- Invoking `tabdat --json doctor` emits standard JSON success envelope containing `DoctorResult` payload.

## Examples
Terminal output:
```text
TabDat 0.23.0 Environment Diagnostics

Core Capabilities:
  DuckDB        ✓ 1.4.3
  PyArrow       ✓ 24.0.0
  Polars        ✓ 1.36.1
  Plotting      ✓ altair 6.1.0, matplotlib 3.10.9

Statistics:
  statsmodels   ✓ 0.14.6
  linearmodels  ✓ 7.0
  scipy         ✓ 1.15.0

Optional Capabilities:
  ML            ✓ scikit-learn 1.7.0
  Bayesian      ✓ bambi 0.18.0
  Spatial       ✓ spreg 1.4.0, libpysal 4.12.1
  R             ✓ rpy2 3.6.4

System:
  Python        3.13.1
  Platform      Darwin (arm64)
```

## Acceptance Criteria
- [ ] `DoctorCommand` AST node and `DoctorResult` model defined in `src/tabdat/models.py`.
- [ ] `doctor` command parser in `src/tabdat/parser.py` validates 0 args/options and rejects `by: doctor`.
- [ ] Modular diagnostics inspection engine in `src/tabdat/doctor.py` safely inspects libraries without unhandled crashes.
- [ ] `DoctorResult` text formatter in `src/tabdat/formatter.py` produces clean aligned tabular diagnostics.
- [ ] `tabdat doctor` and `tabdat --json doctor` supported from CLI.
- [ ] `doctor.md` in-app help topic added and registered in `src/tabdat/help/topics/`.
- [ ] Docs and `check_docs_alignment.py` pass.
- [ ] Comprehensive unit, executor, and CLI tests added.

# Phase 15 Slice 2-3 Implementation Report

## Scope

Implemented two bounded Phase 15 slices on branch `codex/tmp-phase15-slice2-3-probit-estat-margins`:

- Slice 2: `probit` nonlinear binary-choice estimator core
- Slice 3: `estat margins` after binary-choice estimators

## What Changed

### Parser and shell command surface

- Added `probit <y> <xvars>[, robust cluster(<var>) noconstant]` command parsing.
- Added parser guards for:
  - required outcome plus one-or-more predictors
  - `robust` and `cluster(<var>)` mutual exclusion
  - valid single-variable `cluster(...)` syntax
- Extended `estat` subcommand routing with `margins`.
- Added interactive shell completion support for:
  - `probit` command name, active-dataset columns, and options
  - `estat margins` completion.

### Executor and formatting

- Added bounded `statsmodels`-based `probit` execution with covariance modes:
  - nonrobust (default)
  - robust (`HC1`)
  - clustered (`cluster(<var>)`)
- Added complete-case sample extraction and guards for:
  - missing active dataset
  - missing variables
  - non-numeric variables
  - non-binary outcome (must be `0/1`)
  - empty complete-case sample
  - incomplete cluster values in clustered mode
- Added deterministic `probit` formatter output with:
  - model header
  - covariance label
  - observation count
  - pseudo R-squared
  - coefficient table (`Coef`, `Std Err`, `z`, `P>|z|`)
- Added `estat margins` execution for the latest `logit`/`probit` state with deterministic
  predictor-level rows:
  - `dy_dx`, `std_error`, `statistic`, `p_value`, `ci_lower`, `ci_upper`.

### State behavior

- Added binary-estimation state tracking so `estat margins` can run after `logit` or `probit`.
- Preserved existing family boundaries:
  - linear `predict` still requires prior `regress` or `cfregress`
  - existing `estat` flows for linear/IV/panel/control-function remain unchanged.

### Tests

- Added focused parser coverage for valid/invalid `probit` and `estat margins` syntax.
- Added focused shell completion coverage for `probit` and `estat margins`.
- Added focused executor coverage for:
  - typed `probit` result path
  - covariance mode behavior
  - guard/prerequisite errors
  - `estat margins` after `logit` and `probit`
- Added focused CLI coverage for:
  - nonrobust/robust/clustered `probit` runs
  - `estat margins` flow after `logit` and `probit`.

### Documentation and SDD state

- Updated `README.md`, `SPEC.md`, `ARCHITECTURE.md`, and `CHANGELOG.md` for Phase 15 slices 2-3.
- Updated `_workspace` handoff artifacts for this delivery.

## Checkpoint Commits

- `63684de` `feat(phase15): add probit core and estat margins diagnostics`
- `4e9252a` `docs(phase15): record probit and estat margins slices with SDD updates`

## Files Changed

- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/shell.py`
- `src/tabdat/executor.py`
- `src/tabdat/formatter.py`
- `tests/test_parser.py`
- `tests/test_shell.py`
- `tests/test_executor.py`
- `tests/test_cli.py`
- `README.md`
- `SPEC.md`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `_workspace/00_input/request-summary.md`
- `_workspace/01_product_command-contract.md`
- `_workspace/02_implementation_report.md`
- `_workspace/03_qa_report.md`
- `_workspace/final/tabdat-delivery-summary.md`

# Implementation Report: Spatial Autoregressive with Spatial Errors (SARAR / SAC) Support

## Contract Consumed

- `_workspace/01_product_command-contract.md` (Design and requirements for `spregress` combo models).

## Files Changed

- [src/tabdat/models.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/models.py): Added `"sarar"` to the model type literals in `SpregressCommand` and `SpatialRegressionResult`.
- [src/tabdat/parser.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/parser.py): Allowed parsing `model(sarar)` and updated error messages and syntax validations.
- [src/tabdat/executor.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/executor.py): Implemented the GMM estimation calling `spreg.GM_Combo` and `spreg.GM_Combo_Het`. Extracted both spatial coefficients (`rho` and `lambda`) along with their statistics and standard errors, handling cases where standard errors are omitted (non-robust `GM_Combo`).
- [src/tabdat/formatter.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/formatter.py): Formatted the estimator label as `"Spatial Combo (SARAR)"`.
- [src/tabdat/help/topics/spregress.md](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/help/topics/spregress.md): Documented the new option and added examples.
- [tests/test_spregress.py](file:///home/saehwan/repos/tabdat-explore-dev/tests/test_spregress.py): Added syntax parsing tests and robust/non-robust GMM execution tests.

## Implementation Notes by Boundary

### Parser
- Checks that `model(sarar)` is accepted and validates it alongside existing options.

### Executor
- Detects `model_type == "sarar"` and instantiates GMM estimators:
  - If `robust` option is set, uses `GM_Combo_Het` which computes standard errors for `lambda`.
  - If `robust` is not set, uses `GM_Combo` which omits standard errors for `lambda` (represented as `None` in the returned coefficients).

### Formatter
- Correctly formats missing standard errors or stats as `.` in the terminal table.

## Validation Commands and Outcomes

1. **Ruff Linter & Formatter**:
   - Command: `uv run ruff check && uv run ruff format --check`
   - Outcome: `All checks passed!`
2. **Basedpyright Type Safety**:
   - Command: `uv run basedpyright`
   - Outcome: `0 errors, 0 warnings, 0 notes`
3. **Pytest Target Integration Tests**:
   - Command: `uv run pytest tests/test_spregress.py`
   - Outcome: `25 passed`
4. **Full Test Suite Validation**:
   - Command: `uv run pytest`
   - Outcome: `928 passed`

## Known Gaps or Follow-up Work

- Out-of-sample prediction support for `sarar` is deferred.

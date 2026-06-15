# Implementation Report: Classical Statistical & Hypothesis Testing

## Contract Consumed
- `_workspace/01_product_command-contract.md` (Design and requirements for classical hypothesis testing commands `test`, `lincom`, and `ttest` suitable for empirical graduate-level research).

## Files Changed
- [SPEC.md](file:///home/saehwan/repos/tabdat-explore-dev/SPEC.md): Added Phase 21 specifications and deferred Phase 19 future items.
- [src/tabdat/models.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/models.py): Registered `TestCommand`, `LincomCommand`, `TtestCommand` and their respective result types. Added `__test__ = False` to prevent pytest from attempting to collect the commands as tests.
- [src/tabdat/parser.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/parser.py): Added command tokenizers, constraint equation parsers, and command builders for `test`, `lincom`, and `ttest`.
- [src/tabdat/executor.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/executor.py): Implemented the execution logic for Wald/F constraint tests, linear combinations with confidence intervals, and one-sample / paired / independent group t-tests. Added pandas index mapping inside `_get_active_estimation_results` to translate default numeric parameter indices back to user-defined variable names.
- [src/tabdat/formatter.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/formatter.py): Created premium Stata-style visual text formatters for all result classes, adhering to 100-character line-length restrictions.
- [tests/test_parser.py](file:///home/saehwan/repos/tabdat-explore-dev/tests/test_parser.py): Added command syntax parsing tests.
- [tests/test_statistical_testing.py](file:///home/saehwan/repos/tabdat-explore-dev/tests/test_statistical_testing.py): Created comprehensive integration tests for OLS constraint testing, linear combinations, and all t-test variants (one-sample, paired, equal variance, and Welch's unequal variance).

## Implementation Notes by Boundary

### Parser
- Constraints are parsed using standard token scanning. Multiple constraints are grouped by parentheses, e.g. `test (x1 = x2) (x3 = 0)`.
- `lincom` expressions are parsed as standard linear formulas.
- `ttest` options are parsed to support `by(varname)` grouping and `welch`/`unequal` variance modes.

### Executor
- **State retrieval**: Parameter estimates and variance covariance matrices are retrieved from statsmodels/linearmodels results in `_get_active_estimation_results`. The returned objects are automatically mapped to original variable names using the active model's predictor names cache.
- **Hypothesis Evaluation**: Restrictions are mapped to restriction matrix $R$ and target vector $r$ by evaluating constraints at zero and coordinate vectors. Wald statistics are computed using NumPy matrix multiplication.
- **T-tests**: Calculated with SciPy's probability distributions, supporting Welch's standard error and Welch-Satterthwaite degrees of freedom approximation.

### Formatter
- Output formats mimic classic Stata visuals, using single-column confidence intervals `[95% Conf. Interval]` and printing test outcomes for all three alternative hypotheses (left-tailed, two-sided, right-tailed) in t-tests.

## Validation Commands and Outcomes
1. **Ruff Linter**:
   - Command: `uv run ruff check`
   - Outcome: `All checks passed!`
2. **Ruff Formatter**:
   - Command: `uv run ruff format`
   - Outcome: `All checks passed!`
3. **Basedpyright Type Safety**:
   - Command: `uv run basedpyright`
   - Outcome: `0 errors, 0 warnings, 0 notes`
4. **Pytest Parser Unit Tests**:
   - Command: `uv run pytest tests/test_parser.py -k test_parse_statistical_testing_commands`
   - Outcome: `1 passed`
5. **Pytest Executor Integration Tests**:
   - Command: `uv run pytest tests/test_statistical_testing.py`
   - Outcome: `4 passed`
6. **Full Test Suite Validation**:
   - Command: `uv run pytest`
   - Outcome: `922 passed`

## Known Gaps or Follow-up Work
- Non-linear constraint post-estimation testing (`testnl`, `nlcom`) is deferred as specified.
- ANOVA and non-parametric t-test fallbacks are currently out of scope.

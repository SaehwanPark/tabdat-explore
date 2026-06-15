import math
from pathlib import Path

import duckdb
import pytest

from tabdat.errors import ExecutionError
from tabdat.executor import Executor
from tabdat.models import (
  BinaryExpression,
  IdentifierExpression,
  IvRegressCommand,
  LincomCommand,
  LincomResult,
  NumberExpression,
  RegressCommand,
  TestCommand,
  TestResult,
  TtestCommand,
  TtestResult,
  UseCommand,
)


def _write_sql_parquet(path: Path, query: str) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(f"copy ({query}) to ? (format parquet)", [str(path)])
  finally:
    connection.close()


def _write_testing_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
      select * from (
        values
          (1.0, 10.0, 5.0, 'group1'),
          (2.0, 12.0, 6.0, 'group1'),
          (3.0, 15.0, 8.0, 'group2'),
          (4.0, 18.0, 9.0, 'group2'),
          (5.0, 20.0, 11.0, 'group1'),
          (6.0, 25.0, 12.0, 'group2')
      ) as test_data(x1, x2, y, grp)
      """,
  )


def test_wald_and_f_tests(tmp_path: Path) -> None:
  path = tmp_path / "data.parquet"
  _write_testing_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x1", "x2")))

    # 1. Joint significance test: test x1 x2
    res_joint = executor.execute(
      TestCommand((IdentifierExpression("x1"), IdentifierExpression("x2")))
    )
    assert isinstance(res_joint, TestResult)
    assert res_joint.df == 2
    assert res_joint.df_residual == 3
    assert not res_joint.is_chi2
    assert res_joint.statistic > 0.0
    assert 0.0 <= res_joint.p_value <= 1.0

    # 2. Single constraint: test x1 = x2 (which evaluates x1 - x2 = 0)
    res_eq = executor.execute(
      TestCommand((BinaryExpression(IdentifierExpression("x1"), "-", IdentifierExpression("x2")),))
    )
    assert isinstance(res_eq, TestResult)
    assert res_eq.df == 1
    assert res_eq.df_residual == 3
    assert abs(res_eq.statistic) >= 0.0

    # 3. Parentheses multiple constraints: test (x1 = x2) (x2 = 2)
    # x2 = 2 constraint parses as x2 - 2.0
    res_multi = executor.execute(
      TestCommand(
        (
          BinaryExpression(IdentifierExpression("x1"), "-", IdentifierExpression("x2")),
          BinaryExpression(IdentifierExpression("x2"), "-", NumberExpression(2.0)),
        )
      )
    )
    assert isinstance(res_multi, TestResult)
    assert res_multi.df == 2
    assert res_multi.df_residual == 3

  finally:
    executor.close()


def test_lincom_estimation(tmp_path: Path) -> None:
  path = tmp_path / "data.parquet"
  _write_testing_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x1", "x2")))

    # lincom x1 - x2
    res = executor.execute(
      LincomCommand(BinaryExpression(IdentifierExpression("x1"), "-", IdentifierExpression("x2")))
    )
    assert isinstance(res, LincomResult)
    assert res.label == "(x1 - x2)"
    assert not math.isnan(res.estimate)
    assert res.standard_error >= 0.0
    assert 0.0 <= res.p_value <= 1.0
    assert res.ci_lower <= res.estimate <= res.ci_upper

  finally:
    executor.close()


def test_ttests(tmp_path: Path) -> None:
  path = tmp_path / "data.parquet"
  _write_testing_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))

    # 1. One-sample t-test: ttest x1 == 3
    res_one = executor.execute(TtestCommand(varname1="x1", value=3.0))
    assert isinstance(res_one, TtestResult)
    assert res_one.null_value == 3.0
    assert res_one.group1_stats.obs == 6
    assert res_one.group1_stats.mean == 3.5
    assert not res_one.is_paired
    assert not res_one.is_welch
    assert 0.0 <= res_one.p_two <= 1.0

    # 2. Paired t-test: ttest x1 == x2
    res_paired = executor.execute(TtestCommand(varname1="x1", varname2="x2"))
    assert isinstance(res_paired, TtestResult)
    assert res_paired.is_paired
    assert res_paired.group1_stats.obs == 6
    assert res_paired.group2_stats is not None
    assert res_paired.group2_stats.obs == 6

    # 3. Two-sample independent t-test (equal variance): ttest x1, by(grp)
    res_two = executor.execute(TtestCommand(varname1="x1", by_variable="grp", welch=False))
    assert isinstance(res_two, TtestResult)
    assert not res_two.is_paired
    assert not res_two.is_welch
    assert res_two.group1_stats.name == "group1"
    assert res_two.group2_stats is not None
    assert res_two.group2_stats.name == "group2"
    # group1 mean (1,2,5) -> 8/3 = 2.6666, group2 mean (3,4,6) -> 13/3 = 4.3333
    assert abs(res_two.difference_stats.mean - (2.6666666666666665 - 4.333333333333333)) < 1e-7

    # 4. Two-sample independent t-test (Welch/unequal variance): ttest x1, by(grp) welch
    res_welch = executor.execute(TtestCommand(varname1="x1", by_variable="grp", welch=True))
    assert isinstance(res_welch, TtestResult)
    assert res_welch.is_welch

  finally:
    executor.close()


def test_testing_unsupported_state_fails(tmp_path: Path) -> None:
  executor = Executor()
  try:
    # 1. No active dataset or estimation results
    with pytest.raises(ExecutionError, match="no active estimation results found"):
      executor.execute(TestCommand((IdentifierExpression("x1"),)))

    with pytest.raises(ExecutionError, match="no active estimation results found"):
      executor.execute(LincomCommand(IdentifierExpression("x1")))

    # 2. Testing variable not in model
    path = tmp_path / "data.parquet"
    _write_testing_parquet(path)
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x1",)))

    with pytest.raises(ExecutionError, match="variable 'x2' not found"):
      executor.execute(TestCommand((IdentifierExpression("x2"),)))

    with pytest.raises(ExecutionError, match="variable 'x2' not found"):
      executor.execute(LincomCommand(IdentifierExpression("x2")))

  finally:
    executor.close()


def test_ttest_zero_variance(tmp_path: Path) -> None:
  path = tmp_path / "const_data.parquet"
  # Write all constant values so standard errors are 0
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (2.0, 2.0, 'group1'),
        (2.0, 2.0, 'group1'),
        (2.0, 2.0, 'group2'),
        (2.0, 2.0, 'group2')
    ) as test_data(x1, x2, grp)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))

    # 1. One-sample t-test with zero variance
    res_one = executor.execute(TtestCommand(varname1="x1", value=2.0))
    assert isinstance(res_one, TtestResult)
    assert math.isnan(res_one.t_statistic)
    assert math.isnan(res_one.p_two)
    assert res_one.group1_stats.mean == 2.0
    assert res_one.group1_stats.ci_lower == 2.0
    assert res_one.group1_stats.ci_upper == 2.0

    # 2. Paired t-test with zero variance
    res_paired = executor.execute(TtestCommand(varname1="x1", varname2="x2"))
    assert isinstance(res_paired, TtestResult)
    assert math.isnan(res_paired.t_statistic)
    assert res_paired.difference_stats.mean == 0.0
    assert res_paired.difference_stats.ci_lower == 0.0
    assert res_paired.difference_stats.ci_upper == 0.0

    # 3. Two-sample t-test (equal variance) with zero variance
    res_two = executor.execute(TtestCommand(varname1="x1", by_variable="grp", welch=False))
    assert isinstance(res_two, TtestResult)
    assert math.isnan(res_two.t_statistic)
    assert res_two.difference_stats.mean == 0.0
    assert res_two.difference_stats.ci_lower == 0.0
    assert res_two.difference_stats.ci_upper == 0.0

    # 4. Two-sample t-test (Welch) with zero variance
    res_welch = executor.execute(TtestCommand(varname1="x1", by_variable="grp", welch=True))
    assert isinstance(res_welch, TtestResult)
    assert math.isnan(res_welch.t_statistic)
    assert res_welch.difference_stats.mean == 0.0
    assert res_welch.difference_stats.ci_lower == 0.0
    assert res_welch.difference_stats.ci_upper == 0.0

  finally:
    executor.close()


def test_nonlinear_constraints_rejected(tmp_path: Path) -> None:
  path = tmp_path / "data.parquet"
  _write_testing_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x1", "x2")))

    # x1 * x2 is nonlinear coefficient product, should fail
    expr_mult = BinaryExpression(IdentifierExpression("x1"), "*", IdentifierExpression("x2"))
    with pytest.raises(
      ExecutionError, match="nonlinear coefficient multiplication is not supported"
    ):
      executor.execute(LincomCommand(expr_mult))

    with pytest.raises(
      ExecutionError, match="nonlinear coefficient multiplication is not supported"
    ):
      executor.execute(TestCommand((expr_mult,)))

    # x1 / x2 is nonlinear coefficient division, should fail
    expr_div = BinaryExpression(IdentifierExpression("x1"), "/", IdentifierExpression("x2"))
    with pytest.raises(ExecutionError, match="nonlinear coefficient division is not supported"):
      executor.execute(LincomCommand(expr_div))

    # Scalar multiplication (e.g. 2 * x1 or x1 * 2) is linear and should succeed
    expr_scalar = BinaryExpression(NumberExpression(2.0), "*", IdentifierExpression("x1"))
    res = executor.execute(LincomCommand(expr_scalar))
    assert isinstance(res, LincomResult)

    expr_scalar_right = BinaryExpression(IdentifierExpression("x1"), "*", NumberExpression(2.0))
    res2 = executor.execute(LincomCommand(expr_scalar_right))
    assert isinstance(res2, LincomResult)

  finally:
    executor.close()


def test_ttest_signed_null_values() -> None:
  from tabdat.parser import parse_command

  cmd1 = parse_command("ttest x == -1")
  assert isinstance(cmd1, TtestCommand)
  assert cmd1.value == -1.0

  cmd2 = parse_command("ttest x == +2.5")
  assert isinstance(cmd2, TtestCommand)
  assert cmd2.value == 2.5


def test_ivregress_post_estimation(tmp_path: Path) -> None:
  path = tmp_path / "data_iv.parquet"
  _write_sql_parquet(
    path,
    """
      select * from (
        values
          (1.0, 10.0, 5.0, 2.0),
          (2.0, 12.0, 6.0, 3.0),
          (3.0, 15.0, 8.0, 4.0),
          (4.0, 18.0, 9.0, 5.0),
          (5.0, 20.0, 11.0, 6.0),
          (6.0, 25.0, 12.0, 7.0)
      ) as test_data(x1, x2, y, z)
      """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    # Run ivregress 2sls y, endog(x1) iv(z) predictors(x2)
    executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("x2",),
        endogenous="x1",
        instruments=("z",),
      )
    )

    # Test coefficient for x1 (endogenous) and x2
    res_x1 = executor.execute(LincomCommand(IdentifierExpression("x1")))
    assert isinstance(res_x1, LincomResult)
    assert not math.isnan(res_x1.estimate)
    assert not math.isnan(res_x1.standard_error)

    res_x2 = executor.execute(LincomCommand(IdentifierExpression("x2")))
    assert isinstance(res_x2, LincomResult)
    assert not math.isnan(res_x2.estimate)
    assert not math.isnan(res_x2.standard_error)

  finally:
    executor.close()

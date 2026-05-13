import math
from decimal import Decimal
from pathlib import Path

import duckdb
import polars as pl
import pytest

from tabdat.backend import resolve_parquet_source
from tabdat.config import TabDatConfig
from tabdat.errors import (
  ExecutionError,
  NoActiveDatasetError,
  TypeMismatchExecutionError,
  UnknownTableError,
  UnknownVariableError,
)
from tabdat.executor import Executor
from tabdat.models import (
  ActivateResult,
  AppendCommand,
  BarCommand,
  BinaryExpression,
  ByCommand,
  CodebookCommand,
  CodebookResult,
  CollapseCommand,
  CountCommand,
  CountResult,
  DescribeCommand,
  DescribeResult,
  DropCommand,
  EstatCommand,
  ExportCommand,
  ExportResult,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HistogramCommand,
  IdentifierExpression,
  IvRegressCommand,
  IvRegressionResult,
  JoinCommand,
  KeepCommand,
  LoadResult,
  NumberExpression,
  PanelCommand,
  PanelMetadata,
  PanelResult,
  ParsedCommand,
  PlotResult,
  PredictCommand,
  PreviewResult,
  RegressCommand,
  RegressionResult,
  RenameCommand,
  ReplaceCommand,
  ReshapeCommand,
  SaveCommand,
  SaveResult,
  ScatterCommand,
  SelectCommand,
  SetCommand,
  SetResult,
  SqlCommand,
  SqlCreateResult,
  StringExpression,
  SummarizeCommand,
  SummarizeResult,
  TableResult,
  TabulateCommand,
  TailCommand,
  TransformResult,
  UseCommand,
  XtDataCommand,
  XtRegCommand,
  XtRegressionResult,
)


def _write_sql_parquet(path: Path, query: str) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(f"copy ({query}) to ? (format parquet)", [str(path)])
  finally:
    connection.close()


def _write_regression_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0, 'a', 1.0, 1.0),
        (2.0, 14.0, 'a', 1.5, 1.5),
        (3.0, 16.5, 'b', 0.5, 0.5),
        (4.0, 19.0, 'b', 2.0, 2.0),
        (5.0, 21.0, 'c', 1.0, 1.0),
        (6.0, 23.5, 'c', 3.0, 3.0)
    ) as reg_data(x, y, cluster_id, weight, sigma)
    """,
  )


def _write_invalid_weight_regression_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0, 1.0, 1.0),
        (2.0, 14.0, 0.0, 1.0),
        (3.0, 16.5, 1.0, -1.0),
        (4.0, 19.0, 2.0, 1.0)
    ) as reg_data(x, y, weight, sigma)
    """,
  )


def _write_collinear_regression_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 2.0, 5.0),
        (2.0, 4.0, 8.0),
        (3.0, 6.0, 11.0),
        (4.0, 8.0, 14.0),
        (5.0, 10.0, 17.0),
        (6.0, 12.0, 20.0)
    ) as reg_data(x1, x2, y)
    """,
  )


def _write_iv_regression_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 10.0, 1.0, 0.0, 'a'),
        (1.0, 12.0, 2.0, 1.0, 'a'),
        (2.0, 15.0, 2.0, 1.0, 'b'),
        (3.0, 16.0, 4.0, 2.0, 'b'),
        (4.0, 18.0, 4.0, 2.0, 'c'),
        (5.0, 20.0, 6.0, 3.0, 'c'),
        (6.0, 21.0, 6.0, 3.0, 'd'),
        (7.0, 24.0, 8.0, 4.0, 'd')
    ) as iv_data(w, y, x_endog, z_inst, cluster_id)
    """,
  )


def _write_iv_overid_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 10.0, 1.0, 0.0, 2.0, 'a'),
        (1.0, 12.0, 2.0, 1.0, 0.0, 'a'),
        (2.0, 15.0, 2.0, 1.0, 1.0, 'b'),
        (3.0, 16.0, 4.0, 2.0, 0.0, 'b'),
        (4.0, 18.0, 4.0, 2.0, 2.0, 'c'),
        (5.0, 20.0, 6.0, 3.0, 1.0, 'c'),
        (6.0, 21.0, 6.0, 3.0, 3.0, 'd'),
        (7.0, 24.0, 8.0, 4.0, 1.0, 'd')
    ) as iv_data(w, y, x_endog, z_inst, z_inst2, cluster_id)
    """,
  )


def _write_panel_regression_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0, 2.0, 'a'),
        (1, 2021, 11.0, 2.0, 1.0, 'a'),
        (1, 2022, 13.0, 3.0, 2.0, 'a'),
        (2, 2020, 14.0, 1.0, 3.0, 'b'),
        (2, 2021, 15.0, 2.0, 2.0, 'b'),
        (2, 2022, 16.0, 3.0, 3.0, 'b'),
        (3, 2020, 9.0, 1.0, 1.0, 'c'),
        (3, 2021, 10.0, 2.0, 2.0, 'c'),
        (3, 2022, 11.0, 3.0, 1.0, 'c')
    ) as panel_data(firm_id, year, wage, exper, tenure, cluster_id)
    """,
  )


def test_use_loads_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    result = executor.execute(UseCommand(sample_parquet))
  finally:
    executor.close()

  assert isinstance(result, LoadResult)
  assert result.dataset.row_count == 3
  assert result.dataset.column_count == 4
  assert result.dataset.execution_mode == "eager"
  assert result.dataset.lazy_engine is None
  assert [column.name for column in result.dataset.columns] == ["age", "bmi", "sex", "cost"]


@pytest.mark.parametrize("engine", ["duckdb", "polars"])
def test_use_lazy_loads_active_dataset(sample_parquet: Path, engine: str) -> None:
  executor = Executor()
  try:
    result = executor.execute(
      UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=engine)  # type: ignore[arg-type]
    )
  finally:
    executor.close()

  assert isinstance(result, LoadResult)
  assert result.dataset.row_count is None
  assert result.dataset.column_count == 4
  assert result.dataset.execution_mode == "lazy"
  assert result.dataset.lazy_engine == engine


def test_resolve_remote_parquet_source() -> None:
  source = resolve_parquet_source("https://example.com/data.parquet")

  assert source.read_path == "https://example.com/data.parquet"
  assert source.display_path == "https://example.com/data.parquet"
  assert source.is_remote is True


def test_resolve_remote_parquet_source_rejects_unsupported_scheme() -> None:
  with pytest.raises(ExecutionError, match="use remote Parquet supports http, https, and s3 URLs"):
    resolve_parquet_source("ftp://example.com/data.parquet")


def test_resolve_remote_parquet_source_rejects_non_parquet() -> None:
  with pytest.raises(ExecutionError, match="use only supports .parquet files"):
    resolve_parquet_source("https://example.com/data.csv")


def test_failing_lazy_use_preserves_existing_active_dataset(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  corrupt_parquet = tmp_path / "corrupt.parquet"
  corrupt_parquet.write_text("not parquet")
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="use could not read Parquet file"):
      executor.execute(UseCommand(corrupt_parquet, execution_mode="lazy", lazy_engine="duckdb"))
    result = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3


def test_failing_polars_lazy_use_preserves_existing_active_dataset(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  corrupt_parquet = tmp_path / "corrupt.parquet"
  corrupt_parquet.write_text("not parquet")
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="use could not read Parquet file"):
      executor.execute(UseCommand(corrupt_parquet, execution_mode="lazy", lazy_engine="polars"))
    result = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3


@pytest.mark.parametrize("engine", ["duckdb", "polars"])
def test_count_queries_lazy_active_dataset(sample_parquet: Path, engine: str) -> None:
  executor = Executor()
  try:
    executor.execute(
      UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=engine)  # type: ignore[arg-type]
    )
    result = executor.execute(CountCommand())
    active_dataset = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3
  assert active_dataset is not None
  assert active_dataset.execution_mode == "lazy"
  assert active_dataset.lazy_engine == engine


def test_phase_13_regress_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(RegressCommand(outcome="y", predictors=("x",)))
  finally:
    executor.close()

  assert isinstance(result, RegressionResult)
  assert result.estimator == "ols"
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.observation_count == 6
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x"]
  assert result.r_squared is not None
  assert 0.0 <= result.r_squared <= 1.0


def test_phase_13_regress_supports_robust_and_cluster_covariance(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(RegressCommand(outcome="y", predictors=("x",), robust=True))
    clustered = executor.execute(
      RegressCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id")
    )
  finally:
    executor.close()

  assert isinstance(robust, RegressionResult)
  assert robust.estimator == "ols"
  assert robust.covariance == "robust"
  assert isinstance(clustered, RegressionResult)
  assert clustered.estimator == "ols"
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_13_regress_supports_wls_and_gls_estimators(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    wls = executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="wls",
        weight_variable="weight",
      )
    )
    gls = executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="gls",
        weight_variable="sigma",
      )
    )
  finally:
    executor.close()

  assert isinstance(wls, RegressionResult)
  assert wls.estimator == "wls"
  assert wls.covariance == "nonrobust"
  assert isinstance(gls, RegressionResult)
  assert gls.estimator == "gls"
  assert gls.covariance == "nonrobust"


def test_phase_13_regress_supports_weighted_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    wls_cluster = executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="wls",
        weight_variable="weight",
        cluster_variable="cluster_id",
      )
    )
    gls_robust = executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="gls",
        weight_variable="sigma",
        robust=True,
      )
    )
  finally:
    executor.close()

  assert isinstance(wls_cluster, RegressionResult)
  assert wls_cluster.covariance == "cluster(cluster_id)"
  assert isinstance(gls_robust, RegressionResult)
  assert gls_robust.covariance == "robust"


def test_phase_13_regress_rejects_non_positive_weight_or_sigma(tmp_path: Path) -> None:
  path = tmp_path / "invalid-weights.parquet"
  _write_invalid_weight_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(ExecutionError, match="regress requires positive weights values"):
      executor.execute(
        RegressCommand(
          outcome="y",
          predictors=("x",),
          estimator="wls",
          weight_variable="weight",
        )
      )
    with pytest.raises(ExecutionError, match="regress requires positive sigma values"):
      executor.execute(
        RegressCommand(
          outcome="y",
          predictors=("x",),
          estimator="gls",
          weight_variable="sigma",
        )
      )
  finally:
    executor.close()


def test_phase_13_predict_supports_weighted_regression_states(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="wls",
        weight_variable="weight",
      )
    )
    wls_predicted = executor.execute(PredictCommand(target_variable="y_hat_wls"))
    executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="gls",
        weight_variable="sigma",
      )
    )
    gls_residuals = executor.execute(
      PredictCommand(target_variable="y_resid_gls", kind="residuals")
    )
  finally:
    executor.close()

  assert isinstance(wls_predicted, TransformResult)
  assert wls_predicted.message == "Predicted y_hat_wls"
  assert isinstance(gls_residuals, TransformResult)
  assert gls_residuals.message == "Predicted y_resid_gls"


def test_phase_13_predict_adds_linear_predictions_and_residuals(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(RegressCommand(outcome="cost", predictors=("age",)))
    predicted = executor.execute(PredictCommand(target_variable="cost_hat"))
    residuals = executor.execute(PredictCommand(target_variable="cost_resid", kind="residuals"))
    preview = executor.execute(HeadCommand(3))
  finally:
    executor.close()

  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted cost_hat"
  assert [column.name for column in predicted.dataset.columns] == [
    "age",
    "bmi",
    "sex",
    "cost",
    "cost_hat",
  ]
  assert isinstance(residuals, TransformResult)
  assert residuals.message == "Predicted cost_resid"
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age", "bmi", "sex", "cost", "cost_hat", "cost_resid")
  assert preview.rows[0][4] == pytest.approx(100.0)
  assert preview.rows[1][4] == pytest.approx(150.0)
  assert preview.rows[2][4] == pytest.approx(200.0)
  assert preview.rows[0][5] == pytest.approx(0.0)
  assert preview.rows[1][5] == pytest.approx(0.0)
  assert preview.rows[2][5] is None


def test_phase_13_predict_requires_prior_regression(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="predict requires a prior regress model"):
      executor.execute(PredictCommand(target_variable="cost_hat"))
  finally:
    executor.close()


def test_phase_13_estat_residuals_ovtest_and_vif(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))
    residuals = executor.execute(EstatCommand(subcommand="residuals"))
    ovtest = executor.execute(EstatCommand(subcommand="ovtest"))
    vif = executor.execute(EstatCommand(subcommand="vif"))
  finally:
    executor.close()

  assert isinstance(residuals, TableResult)
  assert residuals.headers == ("Metric", "Value")
  assert residuals.rows[0][0] == "count"
  assert isinstance(ovtest, TableResult)
  assert ovtest.headers == ("Metric", "Value")
  assert ovtest.rows[0][0] == "F"
  assert isinstance(vif, TableResult)
  assert vif.headers == ("Variable", "VIF")
  assert vif.rows[0][0] == "x"


def test_phase_13_estat_supports_weighted_regression_states(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="wls",
        weight_variable="weight",
      )
    )
    wls_ovtest = executor.execute(EstatCommand(subcommand="ovtest"))
    executor.execute(
      RegressCommand(
        outcome="y",
        predictors=("x",),
        estimator="gls",
        weight_variable="sigma",
      )
    )
    gls_residuals = executor.execute(EstatCommand(subcommand="residuals"))
  finally:
    executor.close()

  assert isinstance(wls_ovtest, TableResult)
  assert wls_ovtest.headers == ("Metric", "Value")
  assert isinstance(gls_residuals, TableResult)
  assert gls_residuals.headers == ("Metric", "Value")


def test_phase_13_estat_vif_preserves_infinite_values(tmp_path: Path) -> None:
  path = tmp_path / "collinear.parquet"
  _write_collinear_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x1", "x2")))
    result = executor.execute(EstatCommand(subcommand="vif"))
  finally:
    executor.close()

  assert isinstance(result, TableResult)
  assert result.headers == ("Variable", "VIF")
  values_by_variable = {row[0]: row[1] for row in result.rows}
  assert isinstance(values_by_variable["x1"], float) and math.isinf(values_by_variable["x1"])
  assert isinstance(values_by_variable["x2"], float) and math.isinf(values_by_variable["x2"])
  assert isinstance(values_by_variable["mean_vif"], float) and math.isinf(
    values_by_variable["mean_vif"]
  )


def test_phase_13_estat_requires_prior_regression(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="estat requires a prior regress model"):
      executor.execute(EstatCommand(subcommand="ovtest"))
  finally:
    executor.close()


def test_phase_14_ivregress_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
  finally:
    executor.close()

  assert isinstance(result, IvRegressionResult)
  assert result.estimator == "2sls"
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.exogenous == ("w",)
  assert result.endogenous == "x_endog"
  assert result.instruments == ("z_inst",)
  assert result.observation_count == 8
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "w", "x_endog"]
  assert result.r_squared is not None


def test_phase_14_ivregress_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
        robust=True,
      )
    )
    clustered = executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, IvRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, IvRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_14_ivregress_reports_prerequisite_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="ivregress requires an active dataset"):
      executor.execute(
        IvRegressCommand(
          outcome="y",
          exogenous=("w",),
          endogenous="x_endog",
          instruments=("z_inst",),
        )
      )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(
      UnknownVariableError,
      match="ivregress unknown variable: w, x_endog, z_inst",
    ):
      executor.execute(
        IvRegressCommand(
          outcome="cost",
          exogenous=("w",),
          endogenous="x_endog",
          instruments=("z_inst",),
        )
      )
  finally:
    executor.close()


def test_phase_14_ivregress_clears_prior_regress_state(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("w",)))
    executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    with pytest.raises(ExecutionError, match="predict requires a prior regress model"):
      executor.execute(PredictCommand(target_variable="y_hat"))
    with pytest.raises(ExecutionError, match="estat requires a prior regress model"):
      executor.execute(EstatCommand(subcommand="ovtest"))
  finally:
    executor.close()


def test_phase_14_estat_iv_diagnostics(tmp_path: Path) -> None:
  path = tmp_path / "iv-overid.parquet"
  _write_iv_overid_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst", "z_inst2"),
      )
    )
    first_stage = executor.execute(EstatCommand(subcommand="firststage"))
    overid = executor.execute(EstatCommand(subcommand="overid"))
  finally:
    executor.close()

  assert isinstance(first_stage, TableResult)
  assert first_stage.headers == ("Variable", "Metric", "Value")
  assert any(row[1] == "partial_f" for row in first_stage.rows)

  assert isinstance(overid, TableResult)
  assert overid.headers == ("Test", "Metric", "Value")
  assert any(row[0] == "sargan" for row in overid.rows)
  assert any(row[0] == "wooldridge_overid" for row in overid.rows)


def test_phase_14_estat_overid_handles_exact_identification(tmp_path: Path) -> None:
  path = tmp_path / "iv-just-identified.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    overid = executor.execute(EstatCommand(subcommand="overid"))
  finally:
    executor.close()

  assert isinstance(overid, TableResult)
  distributions = {row[0]: row[2] for row in overid.rows if row[1] == "distribution"}
  assert distributions["sargan"] == "not_available"
  assert distributions["wooldridge_overid"] == "not_available"


def test_phase_14_estat_iv_requires_prior_ivregress(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="estat firststage requires a prior ivregress model"):
      executor.execute(EstatCommand(subcommand="firststage"))
    with pytest.raises(ExecutionError, match="estat overid requires a prior ivregress model"):
      executor.execute(EstatCommand(subcommand="overid"))
  finally:
    executor.close()


def test_phase_14_xtreg_returns_typed_result_and_covariance(tmp_path: Path) -> None:
  path = tmp_path / "panel-regression.parquet"
  _write_panel_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    fe_result = executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="fe",
        robust=True,
      )
    )
    re_result = executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="re",
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(fe_result, XtRegressionResult)
  assert fe_result.estimator == "fe"
  assert fe_result.covariance == "robust"
  assert [estimate.name for estimate in fe_result.coefficients] == ["exper", "tenure"]
  assert isinstance(re_result, XtRegressionResult)
  assert re_result.estimator == "re"
  assert re_result.covariance == "cluster(cluster_id)"


def test_phase_14_xtreg_requires_panel_metadata(tmp_path: Path) -> None:
  path = tmp_path / "panel-regression.parquet"
  _write_panel_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(
      ExecutionError,
      match="xtreg requires panel metadata; run panel <id_var> <time_var> first",
    ):
      executor.execute(
        XtRegCommand(
          outcome="wage",
          predictors=("exper",),
          estimator="fe",
        )
      )
  finally:
    executor.close()


def test_phase_14_xtdata_within_between_transforms(tmp_path: Path) -> None:
  path = tmp_path / "panel-regression.parquet"
  _write_panel_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    within_result = executor.execute(
      XtDataCommand(
        variables=("wage",),
        transform="within",
      )
    )
    between_result = executor.execute(
      XtDataCommand(
        variables=("wage",),
        transform="between",
      )
    )
    preview = executor.execute(HeadCommand(limit=3))
  finally:
    executor.close()

  assert isinstance(within_result, TransformResult)
  assert within_result.message == "Applied xtdata within transform"
  assert isinstance(between_result, TransformResult)
  assert between_result.message == "Applied xtdata between transform"
  assert within_result.dataset.panel_metadata == PanelMetadata("firm_id", "year")
  assert between_result.dataset.panel_metadata == PanelMetadata("firm_id", "year")
  assert isinstance(preview, PreviewResult)
  assert "wage_within" in preview.columns
  assert "wage_between" in preview.columns
  wage_index = preview.columns.index("wage")
  within_index = preview.columns.index("wage_within")
  between_index = preview.columns.index("wage_between")
  first_wage_raw = preview.rows[0][wage_index]
  first_within_raw = preview.rows[0][within_index]
  first_between_raw = preview.rows[0][between_index]
  assert isinstance(first_wage_raw, int | float | Decimal)
  assert isinstance(first_within_raw, int | float | Decimal)
  assert isinstance(first_between_raw, int | float | Decimal)
  first_wage = float(first_wage_raw)
  first_within = float(first_within_raw)
  first_between = float(first_between_raw)
  assert first_wage == pytest.approx(10.0)
  assert first_within == pytest.approx(-4.0 / 3.0)
  assert first_between == pytest.approx(34.0 / 3.0)


def test_phase_14_xtdata_guards(sample_parquet: Path, tmp_path: Path) -> None:
  path = tmp_path / "panel-regression.parquet"
  _write_panel_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(
      ExecutionError,
      match="xtdata requires panel metadata; run panel <id_var> <time_var> first",
    ):
      executor.execute(XtDataCommand(variables=("age",), transform="within"))
    executor.execute(PanelCommand("set", "sex", "age"))
    with pytest.raises(TypeMismatchExecutionError, match="xtdata requires numeric variables: sex"):
      executor.execute(XtDataCommand(variables=("sex",), transform="within"))

    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(XtDataCommand(variables=("wage",), transform="within"))
    with pytest.raises(ExecutionError, match="xtdata target already exists: wage_within"):
      executor.execute(XtDataCommand(variables=("wage",), transform="within"))
  finally:
    executor.close()


def test_phase_14_estat_hausman_flow_and_guards(tmp_path: Path) -> None:
  path = tmp_path / "panel-regression.parquet"
  _write_panel_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="fe",
        robust=True,
      )
    )
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="re",
        robust=True,
      )
    )
    hausman = executor.execute(EstatCommand(subcommand="hausman"))
  finally:
    executor.close()

  assert isinstance(hausman, TableResult)
  assert hausman.headers == ("Metric", "Value")
  metrics = {row[0]: row[1] for row in hausman.rows}
  assert isinstance(metrics["chi2"], float)
  assert isinstance(metrics["p_value"], float)
  assert metrics["df"] == 2


def test_phase_14_estat_hausman_requires_matching_specs_and_non_cluster(tmp_path: Path) -> None:
  path = tmp_path / "panel-regression.parquet"
  _write_panel_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="fe",
        robust=True,
      )
    )
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper",),
        estimator="re",
        robust=True,
      )
    )
    with pytest.raises(
      ExecutionError,
      match="estat hausman requires matching xtreg specifications",
    ):
      executor.execute(EstatCommand(subcommand="hausman"))
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="fe",
        robust=True,
      )
    )
    executor.execute(
      ReplaceCommand(
        variable="wage",
        expression=BinaryExpression(
          left=IdentifierExpression("wage"),
          operator="*",
          right=NumberExpression(2),
        ),
      )
    )
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="re",
        robust=True,
      )
    )
    with pytest.raises(
      ExecutionError,
      match="estat hausman requires matching xtreg estimation sample",
    ):
      executor.execute(EstatCommand(subcommand="hausman"))
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper", "tenure"),
        estimator="re",
        cluster_variable="cluster_id",
      )
    )
    with pytest.raises(ExecutionError, match="estat hausman does not support clustered covariance"):
      executor.execute(EstatCommand(subcommand="hausman"))
  finally:
    executor.close()


def test_phase_14_estimation_state_invalidation_across_families(tmp_path: Path) -> None:
  iv_path = tmp_path / "iv-regression.parquet"
  panel_path = tmp_path / "panel-regression.parquet"
  _write_iv_regression_parquet(iv_path)
  _write_panel_regression_parquet(panel_path)
  executor = Executor()
  try:
    executor.execute(UseCommand(iv_path))
    executor.execute(RegressCommand(outcome="y", predictors=("w",)))
    executor.execute(UseCommand(panel_path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exper",),
        estimator="fe",
      )
    )
    with pytest.raises(ExecutionError, match="predict requires a prior regress model"):
      executor.execute(PredictCommand(target_variable="y_hat"))
    with pytest.raises(ExecutionError, match="estat requires a prior regress model"):
      executor.execute(EstatCommand(subcommand="ovtest"))

    executor.execute(UseCommand(iv_path))
    executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    with pytest.raises(
      ExecutionError,
      match="estat hausman requires prior xtreg fe and xtreg re models",
    ):
      executor.execute(EstatCommand(subcommand="hausman"))
  finally:
    executor.close()


def test_phase_11_inner_join_named_table(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand(
        "select sex, avg(bmi) as mean_bmi from active group by sex",
        into="sex_lookup",
      )
    )
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(JoinCommand(table_name="sex_lookup", keys=("sex",)))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.message == "Joined sex_lookup"
  assert result.dataset.row_count == 3
  assert [column.name for column in result.dataset.columns] == [
    "age",
    "bmi",
    "sex",
    "cost",
    "mean_bmi",
  ]
  assert isinstance(preview, PreviewResult)
  assert preview.rows == (
    (30, 22.5, "F", 100.0, 25.0),
    (42, 25.0, "M", 150.0, 25.0),
    (54, 27.5, "F", None, 25.0),
  )


def test_phase_11_left_join_preserves_active_rows(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand(
        "select 'F' as sex, 'matched' as label from active limit 1",
        into="female_lookup",
      )
    )
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(JoinCommand(table_name="female_lookup", keys=("sex",), how="left"))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.row_count == 3
  assert isinstance(preview, PreviewResult)
  assert preview.rows == (
    (30, 22.5, "F", 100.0, "matched"),
    (42, 25.0, "M", 150.0, None),
    (54, 27.5, "F", None, "matched"),
  )


def test_phase_11_join_supports_multiple_keys_and_collision_suffix(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand(
        "select sex, age, cost, age + 1 as next_age from active",
        into="lookup",
      )
    )
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(
      JoinCommand(table_name="lookup", keys=("sex", "age"), suffix="_lookup")
    )
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.row_count == 3
  assert [column.name for column in result.dataset.columns] == [
    "age",
    "bmi",
    "sex",
    "cost",
    "cost_lookup",
    "next_age",
  ]


def test_phase_11_join_suffixing_keeps_output_names_unique(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(SqlCommand("select sex, cost from active", into="lookup"))
    executor.execute(UseCommand(sample_parquet))
    executor.execute(GenerateCommand("cost_lookup", NumberExpression(1)))
    result = executor.execute(JoinCommand(table_name="lookup", keys=("sex",), suffix="_lookup"))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert [column.name for column in result.dataset.columns] == [
    "age",
    "bmi",
    "sex",
    "cost",
    "cost_lookup",
    "cost_lookup_2",
  ]


def test_phase_11_join_reports_table_and_key_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="join requires an active dataset"):
      executor.execute(JoinCommand(table_name="lookup", keys=("id",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownTableError, match="unknown table: lookup"):
      executor.execute(JoinCommand(table_name="lookup", keys=("sex",)))
    executor.execute(
      SqlCommand(
        "select sex, count(*) as n from active group by sex",
        into="lookup",
      )
    )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="join unknown variable: missing"):
      executor.execute(JoinCommand(table_name="lookup", keys=("missing",)))
    with pytest.raises(UnknownVariableError, match="join unknown variable in lookup: age"):
      executor.execute(JoinCommand(table_name="lookup", keys=("age",)))
  finally:
    executor.close()


def test_phase_11_append_named_table_aligns_columns_by_active_order(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand(
        "select sex, cost, bmi, age from active where age > 42",
        into="followup",
      )
    )
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(AppendCommand(table_name="followup"))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.message == "Appended followup"
  assert result.dataset.row_count == 4
  assert [column.name for column in result.dataset.columns] == ["age", "bmi", "sex", "cost"]
  assert isinstance(preview, PreviewResult)
  assert preview.rows == (
    (30, 22.5, "F", 100.0),
    (42, 25.0, "M", 150.0),
    (54, 27.5, "F", None),
    (54, 27.5, "F", None),
  )


def test_phase_11_append_preserves_active_named_table_snapshot(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(SqlCommand("select * from active where age = 30", into="base"))
    executor.execute(UseCommand(sample_parquet))
    executor.execute(SqlCommand("select * from active where age = 42", into="followup"))
    executor.execute(UseCommand(Path("base")))
    result = executor.execute(AppendCommand(table_name="followup"))
    appended_count = executor.execute(CountCommand())
    executor.execute(UseCommand(Path("base")))
    base_count = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.row_count == 2
  assert isinstance(appended_count, CountResult)
  assert appended_count.row_count == 2
  assert isinstance(base_count, CountResult)
  assert base_count.row_count == 1


def test_phase_11_append_reports_table_schema_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="append requires an active dataset"):
      executor.execute(AppendCommand(table_name="followup"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownTableError, match="unknown table: followup"):
      executor.execute(AppendCommand(table_name="followup"))
    executor.execute(SqlCommand("select age, bmi, sex from active", into="missing_cost"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="append unknown variable in missing_cost: cost"):
      executor.execute(AppendCommand(table_name="missing_cost"))
    executor.execute(SqlCommand("select *, 1 as extra from active", into="extra_column"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="append unknown variable: extra"):
      executor.execute(AppendCommand(table_name="extra_column"))
    executor.execute(
      SqlCommand("select cast(age as varchar) as age, bmi, sex, cost from active", into="bad_type")
    )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(TypeMismatchExecutionError, match="append type mismatch for age"):
      executor.execute(AppendCommand(table_name="bad_type"))
  finally:
    executor.close()


def test_phase_11_reshape_long_wide_roundtrip(tmp_path: Path) -> None:
  path = tmp_path / "wide.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 10.0, 12.0, 100.0, 120.0),
        (2, 20.0, 21.0, 200.0, 210.0)
    ) as wide(id, income_2020, income_2021, cost_2020, cost_2021)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    long_result = executor.execute(
      ReshapeCommand(
        direction="long",
        variables=("income", "cost"),
        identifiers=("id",),
        j_variable="year",
      )
    )
    long_preview = executor.execute(HeadCommand(5))
    wide_result = executor.execute(
      ReshapeCommand(
        direction="wide",
        variables=("income", "cost"),
        identifiers=("id",),
        j_variable="year",
      )
    )
    wide_preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(long_result, TransformResult)
  assert long_result.message == "Reshaped long"
  assert [column.name for column in long_result.dataset.columns] == ["id", "year", "income", "cost"]
  assert long_result.dataset.row_count == 4
  assert isinstance(long_preview, PreviewResult)
  assert long_preview.rows == (
    (1, "2020", 10.0, 100.0),
    (1, "2021", 12.0, 120.0),
    (2, "2020", 20.0, 200.0),
    (2, "2021", 21.0, 210.0),
  )
  assert isinstance(wide_result, TransformResult)
  assert wide_result.message == "Reshaped wide"
  assert [column.name for column in wide_result.dataset.columns] == [
    "id",
    "income_2020",
    "income_2021",
    "cost_2020",
    "cost_2021",
  ]
  assert wide_result.dataset.row_count == 2
  assert isinstance(wide_preview, PreviewResult)
  assert wide_preview.rows == (
    (1, 10.0, 12.0, 100.0, 120.0),
    (2, 20.0, 21.0, 200.0, 210.0),
  )


def test_phase_11_reshape_reports_dataset_and_variable_errors(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  path = tmp_path / "partial.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 10.0, 12.0, 100.0, '2020', 10.0),
        (2, 20.0, 21.0, 200.0, '2021', 20.0)
    ) as partial(id, income_2020, income_2021, cost_2020, year, income)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="reshape requires an active dataset"):
      executor.execute(ReshapeCommand("long", ("income",), identifiers=("id",), j_variable="year"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="reshape unknown variable: id"):
      executor.execute(ReshapeCommand("long", ("income",), identifiers=("id",), j_variable="year"))
    executor.execute(UseCommand(path))
    with pytest.raises(ExecutionError, match="reshape output column already exists: year"):
      executor.execute(ReshapeCommand("long", ("income",), identifiers=("id",), j_variable="year"))
    executor.execute(DropCommand(("year", "income")))
    with pytest.raises(UnknownVariableError, match="reshape long found no columns for stub: bmi"):
      executor.execute(ReshapeCommand("long", ("bmi",), identifiers=("id",), j_variable="year"))
    with pytest.raises(UnknownVariableError, match="reshape long missing column: cost_2021"):
      executor.execute(
        ReshapeCommand(
          "long",
          ("income", "cost"),
          identifiers=("id",),
          j_variable="year",
        )
      )
  finally:
    executor.close()


def test_phase_11_reshape_long_validates_j_values_across_all_stubs(tmp_path: Path) -> None:
  path = tmp_path / "ragged_wide.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 10.0, 100.0, 300.0),
        (2, 20.0, 200.0, 400.0)
    ) as ragged(id, income_2020, cost_2020, cost_2022)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(UnknownVariableError, match="reshape long missing column: income_2022"):
      executor.execute(
        ReshapeCommand(
          "long",
          ("income", "cost"),
          identifiers=("id",),
          j_variable="year",
        )
      )
  finally:
    executor.close()


def test_phase_11_reshape_wide_reports_output_conflict(tmp_path: Path) -> None:
  path = tmp_path / "long_conflict.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, '2020', 10.0, 999.0),
        (1, '2021', 12.0, 999.0)
    ) as long_data(id, year, income, income_2020)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(ExecutionError, match="reshape wide output column already exists"):
      executor.execute(
        ReshapeCommand(
          "wide",
          ("income",),
          identifiers=("id",),
          j_variable="year",
        )
      )
  finally:
    executor.close()


def test_phase_11_panel_set_report_clear_and_named_table_restore(tmp_path: Path) -> None:
  path = tmp_path / "panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0),
        (1, 2021, 12.0),
        (2, 2020, 20.0)
    ) as panel_data(firm_id, year, income)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    report_before = executor.execute(PanelCommand(action="report"))
    executor.execute(SqlCommand("select * from active", into="snapshot"))
    set_result = executor.execute(PanelCommand("set", "firm_id", "year"))
    report_after = executor.execute(PanelCommand(action="report"))
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="clear"))
    cleared = executor.execute(PanelCommand(action="report"))
    executor.execute(UseCommand(Path("snapshot")))
    restored = executor.execute(PanelCommand(action="report"))
  finally:
    executor.close()

  assert report_before == PanelResult(action="report")
  assert set_result == PanelResult("set", PanelMetadata("firm_id", "year"))
  assert report_after == PanelResult("report", PanelMetadata("firm_id", "year"))
  assert cleared == PanelResult(action="report")
  assert restored == PanelResult("report", PanelMetadata("firm_id", "year"))


def test_phase_11_panel_reports_validation_errors(sample_parquet: Path, tmp_path: Path) -> None:
  bad_path = tmp_path / "bad_panel.parquet"
  _write_sql_parquet(
    bad_path,
    """
    select * from (
      values
        (1, 2020, 10.0),
        (1, 2020, 12.0),
        (2, null, 20.0)
    ) as panel_data(firm_id, year, income)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="panel requires an active dataset"):
      executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="panel unknown variable: firm_id"):
      executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(UseCommand(bad_path))
    with pytest.raises(ExecutionError, match="panel variables cannot contain missing values: year"):
      executor.execute(PanelCommand("set", "firm_id", "year"))
    executor.execute(
      DropCommand(
        condition=BinaryExpression(
          IdentifierExpression("firm_id"),
          "==",
          NumberExpression(2),
        )
      )
    )
    with pytest.raises(ExecutionError, match="panel id/time pairs must be unique"):
      executor.execute(PanelCommand("set", "firm_id", "year"))
  finally:
    executor.close()


def test_phase_11_panel_metadata_preservation_and_clearing(tmp_path: Path) -> None:
  path = tmp_path / "panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0),
        (1, 2021, 12.0),
        (2, 2020, 20.0)
    ) as panel_data(firm_id, year, income)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    kept_rows = executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          IdentifierExpression("income"),
          ">",
          NumberExpression(10),
        )
      )
    )
    renamed = executor.execute(RenameCommand("firm_id", "id"))
    generated = executor.execute(
      GenerateCommand(
        "double_income",
        BinaryExpression(IdentifierExpression("income"), "*", NumberExpression(2)),
      )
    )
    selected = executor.execute(SelectCommand(("id", "year", "double_income")))
    dropped = executor.execute(DropCommand(("year",)))
  finally:
    executor.close()

  assert isinstance(kept_rows, TransformResult)
  assert kept_rows.dataset.panel_metadata == PanelMetadata("firm_id", "year")
  assert isinstance(renamed, TransformResult)
  assert renamed.dataset.panel_metadata == PanelMetadata("id", "year")
  assert isinstance(generated, TransformResult)
  assert generated.dataset.panel_metadata == PanelMetadata("id", "year")
  assert isinstance(selected, TransformResult)
  assert selected.dataset.panel_metadata == PanelMetadata("id", "year")
  assert isinstance(dropped, TransformResult)
  assert dropped.dataset.panel_metadata is None


def test_phase_11_panel_metadata_revalidates_replace_and_clears_materializers(
  tmp_path: Path,
) -> None:
  path = tmp_path / "panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0),
        (1, 2021, 12.0)
    ) as panel_data(firm_id, year, income)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    with pytest.raises(ExecutionError, match="panel id/time pairs must be unique"):
      executor.execute(ReplaceCommand("year", NumberExpression(2020)))
    preview_after_failed_replace = executor.execute(HeadCommand(5))
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand("set", "firm_id", "year"))
    collapsed = executor.execute(CollapseCommand("mean", ("income",), ("firm_id",)))
  finally:
    executor.close()

  assert isinstance(preview_after_failed_replace, PreviewResult)
  assert preview_after_failed_replace.rows == ((1, 2020, 10.0), (1, 2021, 12.0))
  assert isinstance(collapsed, TransformResult)
  assert collapsed.dataset.panel_metadata is None


@pytest.mark.parametrize("engine", ["duckdb", "polars"])
def test_lazy_transformations_compose_before_terminal_results(
  sample_parquet: Path,
  engine: str,
) -> None:
  executor = Executor()
  try:
    executor.execute(
      UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=engine)  # type: ignore[arg-type]
    )
    executor.execute(SelectCommand(("age", "sex", "cost")))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    result = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, PreviewResult)
  assert result.columns == ("age", "sex", "cost")
  assert result.rows == ((42, "M", 150.0), (54, "F", None))


def test_describe_requires_active_dataset() -> None:
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match="describe requires an active dataset"):
      executor.execute(DescribeCommand())
  finally:
    executor.close()


def test_describe_returns_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(DescribeCommand())
  finally:
    executor.close()

  assert isinstance(result, DescribeResult)
  assert result.dataset.row_count == 3
  assert result.dataset.columns[0].name == "age"


def test_summarize_requested_numeric_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(SummarizeCommand(("age", "cost")))
  finally:
    executor.close()

  assert isinstance(result, SummarizeResult)
  assert [row.variable for row in result.rows] == ["age", "cost"]
  age = result.rows[0]
  cost = result.rows[1]
  assert age.count == 3
  assert age.mean == 42
  assert age.minimum == 30
  assert age.maximum == 54
  assert cost.count == 2
  assert cost.mean == 125


def test_summarize_without_variables_uses_all_numeric_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(SummarizeCommand(()))
  finally:
    executor.close()

  assert isinstance(result, SummarizeResult)
  assert [row.variable for row in result.rows] == ["age", "bmi", "cost"]


def test_summarize_rejects_missing_column(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="summarize unknown variable: missing"):
      executor.execute(SummarizeCommand(("missing",)))
  finally:
    executor.close()


def test_summarize_rejects_non_numeric_column(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="summarize requires numeric variables: sex"):
      executor.execute(SummarizeCommand(("sex",)))
  finally:
    executor.close()


def test_codebook_profiles_requested_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CodebookCommand(("age", "cost")))
  finally:
    executor.close()

  assert isinstance(result, CodebookResult)
  assert [row.variable for row in result.rows] == ["age", "cost"]
  age = result.rows[0]
  cost = result.rows[1]
  assert age.nonmissing == 3
  assert age.missing == 0
  assert age.distinct == 3
  assert age.examples == (30, 42, 54)
  assert cost.nonmissing == 2
  assert cost.missing == 1
  assert cost.distinct == 2


def test_codebook_without_variables_profiles_all_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CodebookCommand(()))
  finally:
    executor.close()

  assert isinstance(result, CodebookResult)
  assert [row.variable for row in result.rows] == ["age", "bmi", "sex", "cost"]


def test_codebook_rejects_missing_column(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="codebook unknown variable: missing"):
      executor.execute(CodebookCommand(("missing",)))
  finally:
    executor.close()


def test_count_returns_active_dataset_row_count(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3


def test_head_returns_first_rows(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(HeadCommand(2))
  finally:
    executor.close()

  assert isinstance(result, PreviewResult)
  assert result.columns == ("age", "bmi", "sex", "cost")
  assert result.rows == ((30, 22.5, "F", 100.0), (42, 25.0, "M", 150.0))


def test_tail_returns_last_rows(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(TailCommand(2))
  finally:
    executor.close()

  assert isinstance(result, PreviewResult)
  assert result.columns == ("age", "bmi", "sex", "cost")
  assert result.rows == ((42, 25.0, "M", 150.0), (54, 27.5, "F", None))


def test_keep_and_drop_columns_update_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(KeepCommand(variables=("age", "sex")))
    result = executor.execute(DropCommand(variables=("sex",)))
    preview = executor.execute(HeadCommand(1))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.column_count == 1
  assert [column.name for column in result.dataset.columns] == ["age"]
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age",)
  assert preview.rows == ((30,),)


def test_select_and_row_filters_update_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    executor.execute(
      DropCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("sex"),
          operator="==",
          right=StringExpression("M"),
        )
      )
    )
    result = executor.execute(SelectCommand(("age", "cost")))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.row_count == 1
  assert result.dataset.column_count == 2
  assert isinstance(preview, PreviewResult)
  assert preview.rows == ((54, None),)


def test_rename_generate_and_replace_update_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(RenameCommand("sex", "gender"))
    executor.execute(
      GenerateCommand(
        "age_plus_one",
        BinaryExpression(
          left=IdentifierExpression("age"),
          operator="+",
          right=NumberExpression(1),
        ),
      )
    )
    executor.execute(
      ReplaceCommand(
        "cost",
        NumberExpression(0),
        BinaryExpression(
          left=IdentifierExpression("gender"),
          operator="==",
          right=StringExpression("F"),
        ),
      )
    )
    preview = executor.execute(HeadCommand(3))
  finally:
    executor.close()

  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age", "bmi", "gender", "cost", "age_plus_one")
  assert preview.rows == (
    (30, 22.5, "F", 0.0, 31),
    (42, 25.0, "M", 150.0, 43),
    (54, 27.5, "F", 0.0, 55),
  )


def test_tabulate_one_way_and_two_way(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    one_way = executor.execute(TabulateCommand(("sex",)))
    two_way = executor.execute(
      TabulateCommand(("sex", "age"), row_percent=True, column_percent=True)
    )
  finally:
    executor.close()

  assert isinstance(one_way, TableResult)
  assert one_way.headers == ("sex", "Count", "Percent")
  assert one_way.rows == (("F", 2, pytest.approx(66.666666)), ("M", 1, pytest.approx(33.333333)))
  assert isinstance(two_way, TableResult)
  assert two_way.headers == ("sex", "age", "Count", "Row %", "Col %")
  assert two_way.rows[0] == ("F", 30, 1, pytest.approx(50.0), pytest.approx(100.0))


def test_by_summarize_and_count_do_not_change_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    summarized = executor.execute(ByCommand(("sex",), SummarizeCommand(("age",))))
    counted = executor.execute(ByCommand(("sex",), CountCommand()))
    preview = executor.execute(HeadCommand(1))
  finally:
    executor.close()

  assert isinstance(summarized, TableResult)
  assert summarized.headers == ("sex", "mean_age")
  assert summarized.rows == (("F", 42.0), ("M", 42.0))
  assert isinstance(counted, TableResult)
  assert counted.headers == ("sex", "Count")
  assert counted.rows == (("F", 2), ("M", 1))
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age", "bmi", "sex", "cost")


def test_by_summarize_without_varlist_uses_numeric_non_group_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    summarized = executor.execute(ByCommand(("sex",), SummarizeCommand(())))
  finally:
    executor.close()

  assert isinstance(summarized, TableResult)
  assert summarized.headers == ("sex", "mean_age", "mean_bmi", "mean_cost")
  assert summarized.rows == (
    ("F", 42.0, 25.0, 100.0),
    ("M", 42.0, 25.0, 150.0),
  )


def test_collapse_replaces_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CollapseCommand("mean", ("age", "cost"), ("sex",)))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.column_count == 3
  assert [column.name for column in result.dataset.columns] == ["sex", "mean_age", "mean_cost"]
  assert isinstance(preview, PreviewResult)
  assert preview.rows == (("F", 42.0, 100.0), ("M", 42.0, 150.0))


def test_sql_queries_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(
      SqlCommand("select sex, avg(bmi) as mean_bmi from active group by sex order by sex")
    )
  finally:
    executor.close()

  assert isinstance(result, TableResult)
  assert result.headers == ("sex", "mean_bmi")
  assert result.rows == (("F", 25.0), ("M", 25.0))


def test_sql_into_replaces_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(
      SqlCommand(
        "select sex, count(*) as n from active group by sex order by sex",
        into="summary",
      )
    )
    described = executor.execute(DescribeCommand())
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, SqlCreateResult)
  assert result.table_name == "summary"
  assert result.dataset.row_count == 2
  assert [column.name for column in result.dataset.columns] == ["sex", "n"]
  assert isinstance(described, DescribeResult)
  assert [column.name for column in described.dataset.columns] == ["sex", "n"]
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("sex", "n")
  assert preview.rows == (("F", 2), ("M", 1))


def test_sql_into_registers_named_table_for_later_activation(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand(
        "select sex, count(*) as n from active group by sex order by sex",
        into="summary",
      )
    )
    executor.execute(KeepCommand(variables=("sex",)))
    transformed_summary = executor.execute(DescribeCommand())
    activated = executor.execute(UseCommand(Path("summary")))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(transformed_summary, DescribeResult)
  assert [column.name for column in transformed_summary.dataset.columns] == ["sex"]
  assert isinstance(activated, ActivateResult)
  assert activated.table_name == "summary"
  assert [column.name for column in activated.dataset.columns] == ["sex"]
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("sex",)
  assert preview.rows == (("F",), ("M",))


def test_use_unknown_named_table_reports_specific_error() -> None:
  executor = Executor()
  try:
    with pytest.raises(UnknownTableError, match="unknown table: missing_table"):
      executor.execute(UseCommand(Path("missing_table")))
  finally:
    executor.close()


def test_use_named_table_rejects_options(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand("select sex, count(*) as n from active group by sex order by sex", into="summary")
    )
    with pytest.raises(
      ExecutionError,
      match="use options are not supported for named table activation",
    ):
      executor.execute(UseCommand(Path("summary"), execution_mode="lazy", lazy_engine="duckdb"))
  finally:
    executor.close()


def test_sql_reports_user_facing_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="sql requires an active dataset"):
      executor.execute(SqlCommand("select * from active"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="sql only supports select or with queries"):
      executor.execute(SqlCommand("drop table active"))
    with pytest.raises(ExecutionError, match="sql failed"):
      executor.execute(SqlCommand("select missing from active"))
  finally:
    executor.close()


def test_phase_6_visualizations_write_svg_artifacts(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  histogram_path = tmp_path / "plots" / "age.svg"
  scatter_path = tmp_path / "plots" / "bmi-age.svg"
  bar_path = tmp_path / "plots" / "sex.svg"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    histogram = executor.execute(HistogramCommand("age", bins=5, saving=histogram_path))
    scatter = executor.execute(ScatterCommand("bmi", "age", saving=scatter_path))
    bar = executor.execute(BarCommand("sex", saving=bar_path))
  finally:
    executor.close()

  assert isinstance(histogram, PlotResult)
  assert histogram.path == histogram_path
  assert histogram.should_open
  assert histogram_path.read_text().lstrip().startswith("<svg")
  assert isinstance(scatter, PlotResult)
  assert scatter.path == scatter_path
  assert scatter_path.read_text().lstrip().startswith("<svg")
  assert isinstance(bar, PlotResult)
  assert bar.path == bar_path
  assert bar_path.read_text().lstrip().startswith("<svg")


def test_phase_9_set_updates_plot_defaults(sample_parquet: Path, tmp_path: Path) -> None:
  executor = Executor(config=TabDatConfig(artifact_dir=tmp_path / "artifacts"))
  try:
    result = executor.execute(SetCommand("graph_format", "png"))
    executor.execute(UseCommand(sample_parquet))
    plot = executor.execute(HistogramCommand("age"))
  finally:
    executor.close()

  assert isinstance(result, SetResult)
  assert result.value == "png"
  assert isinstance(plot, PlotResult)
  assert plot.path == tmp_path / "artifacts" / "plots" / "histogram-age.png"
  assert plot.path.exists()


def test_phase_9_executor_default_plot_path_remains_stable_on_repeated_saves(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  executor = Executor(config=TabDatConfig(artifact_dir=tmp_path / "artifacts"))
  try:
    executor.execute(UseCommand(sample_parquet))
    first_plot = executor.execute(HistogramCommand("age"))
    second_plot = executor.execute(HistogramCommand("age"))
  finally:
    executor.close()

  assert isinstance(first_plot, PlotResult)
  assert isinstance(second_plot, PlotResult)
  assert first_plot.path == tmp_path / "artifacts" / "plots" / "histogram-age.svg"
  assert second_plot.path == first_plot.path


def test_phase_9_save_writes_transformed_active_dataset(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "filtered.parquet"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    result = executor.execute(SaveCommand(output_path))
    with pytest.raises(ExecutionError, match="save target already exists"):
      executor.execute(SaveCommand(output_path))
    replaced = executor.execute(SaveCommand(output_path, replace=True))
  finally:
    executor.close()

  assert isinstance(result, SaveResult)
  assert result.dataset.row_count == 2
  assert output_path.exists()
  assert isinstance(replaced, SaveResult)


@pytest.mark.parametrize("suffix", [".parquet", ".csv", ".feather"])
def test_phase_9_export_writes_supported_formats(
  sample_parquet: Path,
  tmp_path: Path,
  suffix: str,
) -> None:
  output_path = tmp_path / f"filtered{suffix}"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    result = executor.execute(ExportCommand(output_path))
    with pytest.raises(ExecutionError, match="export target already exists"):
      executor.execute(ExportCommand(output_path))
    replaced = executor.execute(ExportCommand(output_path, replace=True))
  finally:
    executor.close()

  assert isinstance(result, ExportResult)
  assert result.dataset.row_count == 2
  assert output_path.exists()
  assert isinstance(replaced, ExportResult)
  if suffix == ".parquet":
    rows = duckdb.sql(
      "select age, bmi, sex, cost from read_parquet(?)", params=[str(output_path)]
    ).fetchall()
    assert rows == [(42, 25.0, "M", 150.0), (54, 27.5, "F", None)]
  elif suffix == ".csv":
    assert output_path.read_text(encoding="utf-8").splitlines() == [
      "age,bmi,sex,cost",
      "42,25.0,M,150.0",
      "54,27.5,F,",
    ]
  else:
    frame = pl.read_ipc(output_path)
    assert frame.rows() == [(42, 25.0, "M", 150.0), (54, 27.5, "F", None)]


def test_phase_9_export_rejects_unsupported_suffix(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "filtered.json"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(
      ExecutionError,
      match=r"export only supports \.parquet, \.csv, and \.feather files",
    ):
      executor.execute(ExportCommand(output_path))
  finally:
    executor.close()


def test_phase_10_polars_lazy_column_and_row_transforms_preserve_lazy_state(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine="polars"))
    selected = executor.execute(SelectCommand(("age", "sex", "cost")))
    filtered = executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    active_dataset = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(selected, TransformResult)
  assert selected.dataset.execution_mode == "lazy"
  assert selected.dataset.lazy_engine == "polars"
  assert selected.dataset.row_count is None
  assert isinstance(filtered, TransformResult)
  assert filtered.dataset.execution_mode == "lazy"
  assert filtered.dataset.lazy_engine == "polars"
  assert filtered.dataset.row_count is None
  assert active_dataset is not None
  assert active_dataset.execution_mode == "lazy"
  assert active_dataset.lazy_engine == "polars"


def test_phase_10_polars_lazy_unsupported_command_materializes_to_eager(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine="polars"))
    result = executor.execute(GenerateCommand("age2", NumberExpression(2)))
    count = executor.execute(CountCommand())
    active_dataset = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.execution_mode == "eager"
  assert result.dataset.lazy_engine is None
  assert result.dataset.row_count == 3
  assert isinstance(count, CountResult)
  assert count.row_count == 3
  assert active_dataset is not None
  assert active_dataset.execution_mode == "eager"
  assert active_dataset.lazy_engine is None


def test_phase_10_polars_lazy_set_does_not_materialize(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine="polars"))
    result = executor.execute(SetCommand("graph_open", "off"))
    active_dataset = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, SetResult)
  assert result.value == "off"
  assert active_dataset is not None
  assert active_dataset.execution_mode == "lazy"
  assert active_dataset.lazy_engine == "polars"


def test_phase_6_visualizations_report_user_facing_errors(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match="histogram requires an active dataset"):
      executor.execute(HistogramCommand("age"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="plot requires numeric variables: sex"):
      executor.execute(HistogramCommand("sex", saving=tmp_path / "sex.svg"))
    with pytest.raises(ExecutionError, match="plot requires numeric variables: sex"):
      executor.execute(ScatterCommand("age", "sex", saving=tmp_path / "scatter.svg"))
    with pytest.raises(ExecutionError, match="bar unknown variable: missing"):
      executor.execute(BarCommand("missing", saving=tmp_path / "missing.svg"))
    with pytest.raises(ExecutionError, match="plot saving path must end with"):
      executor.execute(HistogramCommand("age", saving=tmp_path / "age.txt"))
  finally:
    executor.close()


def test_phase_3_transformations_report_user_facing_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="generate target already exists: age"):
      executor.execute(GenerateCommand("age", NumberExpression(1)))
    with pytest.raises(ExecutionError, match="replace unknown variable: missing"):
      executor.execute(ReplaceCommand("missing", NumberExpression(1)))
    with pytest.raises(ExecutionError, match="drop would remove every column"):
      executor.execute(DropCommand(("age", "bmi", "sex", "cost")))
    with pytest.raises(ExecutionError, match="unsupported function"):
      executor.execute(GenerateCommand("bad", FunctionCallExpression("not_a_function", ())))
  finally:
    executor.close()


@pytest.mark.parametrize(
  ("command", "message"),
  [
    (CodebookCommand(()), "codebook requires an active dataset"),
    (CountCommand(), "count requires an active dataset"),
    (HeadCommand(), "head requires an active dataset"),
    (TailCommand(), "tail requires an active dataset"),
    (KeepCommand(variables=("age",)), "keep requires an active dataset"),
    (TabulateCommand(("sex",)), "tabulate requires an active dataset"),
  ],
)
def test_phase_3_inspection_commands_require_active_dataset(command, message: str) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match=message):
      executor.execute(command)
  finally:
    executor.close()


def test_unknown_variable_and_type_errors_are_specific(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="summarize unknown variable"):
      executor.execute(SummarizeCommand(("missing",)))
    with pytest.raises(TypeMismatchExecutionError, match="summarize requires numeric variables"):
      executor.execute(SummarizeCommand(("sex",)))
  finally:
    executor.close()


def test_executor_rejects_unsupported_by_child_command() -> None:
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match="unsupported command"):
      executor.execute(ParsedCommand(name="keep"))
  finally:
    executor.close()


def test_use_rejects_non_parquet(tmp_path: Path) -> None:
  csv_path = tmp_path / "patients.csv"
  csv_path.write_text("age\n42\n")
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match=r"\.parquet"):
      executor.execute(UseCommand(csv_path))
  finally:
    executor.close()

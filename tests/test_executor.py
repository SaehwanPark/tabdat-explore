import contextlib
import http.server
import math
import socketserver
import threading
from collections.abc import Iterator
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Any, cast

import duckdb
import polars as pl
import pytest

import tabdat.executor as executor_module
from tabdat.backend import resolve_parquet_source
from tabdat.config import TabDatConfig
from tabdat.errors import (
  ExecutionError,
  NoActiveDatasetError,
  TypeMismatchExecutionError,
  UnknownTableError,
  UnknownVariableError,
)
from tabdat.estimation import CoefficientEstimate
from tabdat.executor import Executor, _xtabond_sample
from tabdat.models import (
  ActivateResult,
  AppendCommand,
  BarCommand,
  BayesCommand,
  BayesRegressionResult,
  BinaryExpression,
  ByCommand,
  CfRegressCommand,
  CfRegressionResult,
  CodebookCommand,
  CodebookResult,
  CollapseCommand,
  CountCommand,
  CountResult,
  DescribeCommand,
  DescribeResult,
  DidCommand,
  DidRegressionResult,
  DropCommand,
  ElasticnetCommand,
  ElasticnetRegressionResult,
  EstatCommand,
  ExportCommand,
  ExportResult,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HeckmanCommand,
  HeckmanRegressionResult,
  HistogramCommand,
  IdentifierExpression,
  IvRegressCommand,
  IvRegressionResult,
  JoinCommand,
  KeepCommand,
  LassoCommand,
  LassoRegressionResult,
  LoadResult,
  LogitCommand,
  LogitRegressionResult,
  LowessCommand,
  NbregCommand,
  NbregRegressionResult,
  NlCommand,
  NlRegressionResult,
  NumberExpression,
  PanelCommand,
  PanelMetadata,
  PanelResult,
  PanelStructureSummary,
  ParsedCommand,
  PlotResult,
  PoissonCommand,
  PoissonRegressionResult,
  PredictCommand,
  PreviewResult,
  ProbitCommand,
  ProbitRegressionResult,
  QregCommand,
  QregRegressionResult,
  RegressCommand,
  RegressionResult,
  RidgeCommand,
  RidgeRegressionResult,
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
  StregCommand,
  StregRegressionResult,
  StringExpression,
  SummarizeCommand,
  SummarizeResult,
  TableResult,
  TabulateCommand,
  TailCommand,
  TobitCommand,
  TobitRegressionResult,
  TransformResult,
  UseCommand,
  XtAbondCommand,
  XtAbondRegressionResult,
  XtDataCommand,
  XtLogitCommand,
  XtLogitRegressionResult,
  XtRegCommand,
  XtRegressionResult,
  ZinbCommand,
  ZinbRegressionResult,
  ZipCommand,
  ZipRegressionResult,
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


def _write_cfresidual_name_collision_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 1.0, 1.0, 8.0),
        (1.0, 1.0, 1.0, 10.0),
        (2.0, 2.0, 2.0, 15.0),
        (3.0, 2.0, 2.0, 17.0),
        (4.0, 3.0, 3.0, 22.0),
        (5.0, 3.0, 3.0, 24.0)
    ) as collision_data(cf_residual, x_endog, z_inst, y)
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


def _write_did_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.2, 0, 0, 1.1),
        (1, 2021, 11.0, 0, 1, 0.8),
        (2, 2020, 9.8, 0, 0, 1.0),
        (2, 2021, 10.7, 0, 1, 1.2),
        (3, 2020, 10.1, 1, 0, 0.9),
        (3, 2021, 12.8, 1, 1, 1.3),
        (4, 2020, 9.9, 1, 0, 1.0),
        (4, 2021, 12.6, 1, 1, 1.1)
    ) as did_data(firm_id, year, wage, treated, post, exposure)
    """,
  )


def _write_xtabond_short_panel_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0),
        (1, 2021, 11.0, 2.0),
        (2, 2020, 9.0, 0.5),
        (2, 2021, 10.0, 1.5)
    ) as panel_data(firm_id, year, wage, exposure)
    """,
  )


def _write_xtabond_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0),
        (1, 2021, 13.0, 2.0),
        (1, 2022, 15.0, 4.0),
        (2, 2020, 7.0, 0.0),
        (2, 2021, 9.0, 1.0),
        (2, 2022, 12.0, 1.5),
        (3, 2020, 20.0, 3.0),
        (3, 2021, 19.0, 2.0),
        (3, 2022, 21.0, 3.0)
    ) as panel_data(firm_id, year, wage, exper)
    """,
  )


def _write_logit_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (0, 22.0, 1.0, 'a'),
        (0, 25.0, 2.0, 'b'),
        (1, 30.0, 2.0, 'b'),
        (1, 34.0, 3.0, 'c'),
        (1, 38.0, 3.0, 'c'),
        (1, 42.0, 4.0, 'd'),
        (1, 45.0, 4.0, 'd')
    ) as logit_data(y, x, z, cluster_id)
    """,
  )


def _write_nonbinary_logit_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0),
        (1, 25.0),
        (2, 30.0),
        (1, 35.0)
    ) as logit_data(y, x)
    """,
  )


def _write_missing_cluster_logit_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 'a'),
        (0, 22.0, null),
        (1, 30.0, 'b'),
        (1, 35.0, 'b')
    ) as logit_data(y, x, cluster_id)
    """,
  )


def _write_poisson_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (1, 22.0, 1.0, 'a'),
        (1, 25.0, 2.0, 'b'),
        (2, 30.0, 2.0, 'b'),
        (3, 34.0, 3.0, 'c'),
        (3, 38.0, 3.0, 'c'),
        (4, 42.0, 4.0, 'd'),
        (5, 45.0, 4.0, 'd')
    ) as poisson_data(y, x, z, cluster_id)
    """,
  )


def _write_nbreg_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (1, 22.0, 1.0, 'a'),
        (1, 25.0, 2.0, 'b'),
        (2, 30.0, 2.0, 'b'),
        (3, 34.0, 3.0, 'c'),
        (3, 38.0, 3.0, 'c'),
        (4, 42.0, 4.0, 'd'),
        (5, 45.0, 4.0, 'd')
    ) as nbreg_data(y, x, z, cluster_id)
    """,
  )


def _write_zero_inflated_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 1.0, 'a'),
        (0, 20.0, 1.0, 2.0, 'a'),
        (1, 25.0, 2.0, 1.0, 'b'),
        (0, 28.0, 2.0, 2.0, 'b'),
        (2, 31.0, 3.0, 1.0, 'c'),
        (0, 35.0, 3.0, 2.0, 'c'),
        (3, 40.0, 4.0, 1.0, 'd'),
        (1, 45.0, 4.0, 2.0, 'd')
    ) as zero_inflated_data(y, x, z, zi, cluster_id)
    """,
  )


def _write_tobit_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 18.0, 1.0, 'a'),
        (0.0, 22.0, 1.0, 'a'),
        (1.5, 25.0, 2.0, 'b'),
        (2.0, 30.0, 2.0, 'b'),
        (4.0, 34.0, 3.0, 'c'),
        (8.0, 38.0, 3.0, 'c'),
        (10.0, 42.0, 4.0, 'd'),
        (10.0, 45.0, 4.0, 'd')
    ) as tobit_data(y, x, z, cluster_id)
    """,
  )


def _write_binary_missing_predictor_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0),
        (0, null, 1.0),
        (1, 30.0, 2.0),
        (1, 34.0, 3.0)
    ) as binary_data(y, x, z)
    """,
  )


def _write_tobit_internal_name_collision_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 18.0, 1.0),
        (0.0, 22.0, 1.0),
        (1.5, 25.0, 2.0),
        (2.0, 30.0, 2.0),
        (4.0, 34.0, 3.0),
        (8.0, 38.0, 3.0),
        (10.0, 42.0, 4.0),
        (10.0, 45.0, 4.0)
    ) as tobit_data(y, tabdat_left, tabdat_right)
    """,
  )


def _write_heckman_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.2, 18.0, 0.2, 0, 'a'),
        (2.1, 22.0, 0.3, 1, 'a'),
        (2.8, 25.0, 0.5, 1, 'b'),
        (3.1, 30.0, 0.7, 1, 'b'),
        (1.0, 34.0, 0.1, 0, 'c'),
        (3.3, 38.0, 0.8, 1, 'c'),
        (0.9, 42.0, 0.2, 0, 'd'),
        (3.5, 45.0, 0.9, 1, 'd')
    ) as heckman_data(y, x, z, s, cluster_id)
    """,
  )


def _write_missing_cluster_heckman_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.2, 18.0, 0.2, 0, 'a'),
        (2.1, 22.0, 0.3, 1, null),
        (2.8, 25.0, 0.5, 1, 'b'),
        (3.1, 30.0, 0.7, 1, 'b')
    ) as heckman_data(y, x, z, s, cluster_id)
    """,
  )


def _write_nl_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 2.718281828),
        (2.0, 7.389056099),
        (3.0, 20.08553692),
        (4.0, 54.59815003),
        (5.0, 148.4131591),
        (null, 403.4287935)
    ) as nl_data(x, y)
    """,
  )


def _write_streg_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 1.0, 30.0, 1.0, 'a'),
        (2.0, 0.0, 35.0, 1.0, 'a'),
        (3.0, 1.0, 40.0, 2.0, 'b'),
        (4.0, 1.0, 28.0, 2.0, 'b'),
        (5.0, 0.0, 50.0, 3.0, 'c'),
        (6.0, 1.0, 45.0, 3.0, 'c'),
        (7.0, 0.0, 33.0, 4.0, 'd'),
        (8.0, 1.0, 38.0, 4.0, 'd')
    ) as streg_data(time, died, age, income, cluster_id)
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


def test_use_loads_local_stata_dataset(sample_dta: Path) -> None:
  executor = Executor()
  try:
    result = executor.execute(UseCommand(sample_dta))
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
  assert source.format == "parquet"
  assert source.is_remote is True


def test_resolve_remote_stata_source() -> None:
  source = resolve_parquet_source("https://example.com/data.dta")

  assert source.read_path == "https://example.com/data.dta"
  assert source.display_path == "https://example.com/data.dta"
  assert source.format == "stata"
  assert source.is_remote is True


def test_resolve_remote_parquet_source_rejects_unsupported_scheme() -> None:
  with pytest.raises(ExecutionError, match="use remote Parquet supports http, https, and s3 URLs"):
    resolve_parquet_source("ftp://example.com/data.parquet")


def test_resolve_remote_parquet_source_rejects_non_parquet() -> None:
  with pytest.raises(ExecutionError, match="use only supports .parquet and .dta files"):
    resolve_parquet_source("https://example.com/data.csv")


def test_resolve_remote_stata_source_rejects_unsupported_scheme() -> None:
  with pytest.raises(ExecutionError, match="use remote Stata files support http and https URLs"):
    resolve_parquet_source("ftp://example.com/data.dta")


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


@contextlib.contextmanager
def _serve_directory(directory: Path) -> Iterator[str]:
  class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
      return

  handler = partial(_SilentHandler, directory=str(directory))
  with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
      yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
      httpd.shutdown()
      thread.join(timeout=2)


def test_use_loads_remote_stata_dataset(sample_dta: Path) -> None:
  executor = Executor()
  try:
    with _serve_directory(sample_dta.parent) as base_url:
      result = executor.execute(UseCommand(f"{base_url}/{sample_dta.name}"))
  finally:
    executor.close()

  assert isinstance(result, LoadResult)
  assert result.dataset.row_count == 3
  assert [column.name for column in result.dataset.columns] == ["age", "bmi", "sex", "cost"]
  assert result.dataset.execution_mode == "eager"
  assert result.dataset.lazy_engine is None


def test_failing_lazy_stata_use_preserves_existing_active_dataset(
  sample_parquet: Path,
  sample_dta: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="use lazy mode only supports Parquet files"):
      executor.execute(UseCommand(sample_dta, execution_mode="lazy", lazy_engine="duckdb"))
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


def test_phase_19_lasso_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "lasso.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      LassoCommand(
        outcome="y",
        predictors=("x",),
        alpha=0.25,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, LassoRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.alpha == pytest.approx(0.25)
  assert result.observation_count == 6
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x"]


def test_phase_19_lasso_predict_supports_xb_only(tmp_path: Path) -> None:
  path = tmp_path / "lasso-predict.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(LassoCommand(outcome="y", predictors=("x",), alpha=0.25))
    predicted = executor.execute(PredictCommand(target_variable="yhat", kind="xb"))
    preview = executor.execute(HeadCommand(1))
    with pytest.raises(ExecutionError, match="predict only supports xb after lasso"):
      executor.execute(PredictCommand(target_variable="resid", kind="residuals"))
    with pytest.raises(ExecutionError, match="predict only supports xb after lasso"):
      executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
  finally:
    executor.close()

  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted yhat"
  assert isinstance(preview, PreviewResult)
  assert "yhat" in preview.columns


def test_phase_19_ridge_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "ridge.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      RidgeCommand(
        outcome="y",
        predictors=("x",),
        alpha=0.25,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, RidgeRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.alpha == pytest.approx(0.25)
  assert result.observation_count == 6
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x"]


def test_phase_19_ridge_predict_supports_xb_only(tmp_path: Path) -> None:
  path = tmp_path / "ridge-predict.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RidgeCommand(outcome="y", predictors=("x",), alpha=0.25))
    predicted = executor.execute(PredictCommand(target_variable="yhat", kind="xb"))
    preview = executor.execute(HeadCommand(1))
    with pytest.raises(ExecutionError, match="predict only supports xb after ridge"):
      executor.execute(PredictCommand(target_variable="resid", kind="residuals"))
    with pytest.raises(ExecutionError, match="predict only supports xb after ridge"):
      executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
  finally:
    executor.close()

  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted yhat"
  assert isinstance(preview, PreviewResult)
  assert "yhat" in preview.columns


def test_phase_19_elasticnet_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "elasticnet.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      ElasticnetCommand(
        outcome="y",
        predictors=("x",),
        alpha=0.25,
        l1_ratio=0.75,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, ElasticnetRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.alpha == pytest.approx(0.25)
  assert result.l1_ratio == pytest.approx(0.75)
  assert result.observation_count == 6
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x"]


def test_phase_19_elasticnet_predict_supports_xb_only(tmp_path: Path) -> None:
  path = tmp_path / "elasticnet-predict.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(ElasticnetCommand(outcome="y", predictors=("x",), alpha=0.25, l1_ratio=0.75))
    predicted = executor.execute(PredictCommand(target_variable="yhat", kind="xb"))
    preview = executor.execute(HeadCommand(1))
    with pytest.raises(ExecutionError, match="predict only supports xb after elasticnet"):
      executor.execute(PredictCommand(target_variable="resid", kind="residuals"))
    with pytest.raises(ExecutionError, match="predict only supports xb after elasticnet"):
      executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
  finally:
    executor.close()

  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted yhat"
  assert isinstance(preview, PreviewResult)
  assert "yhat" in preview.columns


def test_phase_19_bayes_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "bayes.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      BayesCommand(
        outcome="y",
        predictors=("x",),
        n_iter=200,
        tol=1e-4,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, BayesRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.n_iter > 0
  assert result.alpha > 0.0
  assert result.lambda_ > 0.0
  assert result.observation_count == 6
  assert result.include_intercept is True
  assert result.r_squared is not None
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x"]


def test_phase_19_bayes_predict_supports_xb_and_residuals(tmp_path: Path) -> None:
  path = tmp_path / "bayes-predict.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(BayesCommand(outcome="y", predictors=("x",)))
    predicted_xb = executor.execute(PredictCommand(target_variable="yhat", kind="xb"))
    predicted_resid = executor.execute(PredictCommand(target_variable="resid", kind="residuals"))
    preview = executor.execute(HeadCommand(1))

    with pytest.raises(ExecutionError, match="predict only supports xb and residuals after bayes"):
      executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
  finally:
    executor.close()

  assert isinstance(predicted_xb, TransformResult)
  assert isinstance(predicted_resid, TransformResult)
  assert isinstance(preview, PreviewResult)
  assert "yhat" in preview.columns
  assert "resid" in preview.columns


def test_phase_19_bayes_clears_other_regression_states(tmp_path: Path) -> None:
  path = tmp_path / "bayes-state.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))
    assert executor.state.regression is not None
    executor.execute(BayesCommand(outcome="y", predictors=("x",)))
    assert executor.state.regression is None
    assert executor.state.bayes_regression is not None
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))
    assert executor.state.bayes_regression is None
  finally:
    executor.close()


def test_phase_19_failed_heckman_clears_prior_lasso_state(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  path = tmp_path / "lasso-heckman.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0, 0.0, 1.0),
        (2.0, 14.0, 1.0, 1.5),
        (3.0, 16.5, 0.0, 2.0),
        (4.0, 19.0, 1.0, 2.5),
        (5.0, 21.0, 1.0, 3.0),
        (6.0, 23.5, 0.0, 3.5)
    ) as sample(x, y, s, z)
    """,
  )
  monkeypatch.setattr(
    executor_module,
    "_fit_heckman_with_r",
    lambda **_: (_ for _ in ()).throw(ExecutionError("heckman failed")),
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(LassoCommand(outcome="y", predictors=("x",), alpha=0.25))
    with pytest.raises(ExecutionError, match="heckman failed"):
      executor.execute(
        HeckmanCommand(
          outcome="y",
          predictors=("x",),
          selection_dependent="s",
          selection_predictors=("z",),
        )
      )
    with pytest.raises(
      ExecutionError,
      match=(
        "predict requires a prior regress, lasso, ridge, elasticnet, bayes, spregress, qreg, "
        "did, cfregress, nl, poisson, nbreg, zip, or zinb model"
      ),
    ):
      executor.execute(PredictCommand(target_variable="yhat", kind="xb"))
  finally:
    executor.close()


def test_phase_17_qreg_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(QregCommand(outcome="y", predictors=("x",)))
  finally:
    executor.close()

  assert isinstance(result, QregRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.quantile == pytest.approx(0.5)
  assert result.observation_count == 6
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x"]


def test_phase_17_qreg_supports_robust_quantile_predict_and_estat(tmp_path: Path) -> None:
  path = tmp_path / "regression.parquet"
  _write_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      QregCommand(
        outcome="y",
        predictors=("x",),
        quantile=0.25,
        robust=True,
      )
    )
    predicted = executor.execute(PredictCommand(target_variable="qhat", kind="xb"))
    residuals = executor.execute(PredictCommand(target_variable="qresid", kind="residuals"))
    stats = executor.execute(EstatCommand(subcommand="residuals"))
    preview = executor.execute(HeadCommand(1))
  finally:
    executor.close()

  assert isinstance(result, QregRegressionResult)
  assert result.covariance == "robust"
  assert result.quantile == pytest.approx(0.25)
  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted qhat"
  assert isinstance(residuals, TransformResult)
  assert residuals.message == "Predicted qresid"
  assert isinstance(stats, TableResult)
  assert stats.headers == ("Metric", "Value")
  assert stats.rows[0][0] == "count"
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("x", "y", "cluster_id", "weight", "sigma", "qhat", "qresid")


def test_phase_15_nl_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "nl.parquet"
  _write_nl_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      NlCommand(
        outcome="y",
        expression=FunctionCallExpression(
          name="exp",
          arguments=(
            BinaryExpression(
              left=IdentifierExpression("a"),
              operator="+",
              right=BinaryExpression(
                left=IdentifierExpression("b"),
                operator="*",
                right=IdentifierExpression("x"),
              ),
            ),
          ),
        ),
        parameter_names=("a", "b"),
        start_values=(0.5, 0.5),
      )
    )
  finally:
    executor.close()

  assert isinstance(result, NlRegressionResult)
  assert result.outcome == "y"
  assert result.covariance == "nonrobust"
  assert result.observation_count == 5
  assert [estimate.name for estimate in result.coefficients] == ["a", "b"]


def test_phase_15_nl_supports_robust_covariance(tmp_path: Path) -> None:
  path = tmp_path / "nl.parquet"
  _write_nl_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      NlCommand(
        outcome="y",
        expression=FunctionCallExpression(
          name="exp",
          arguments=(
            BinaryExpression(
              left=IdentifierExpression("a"),
              operator="+",
              right=BinaryExpression(
                left=IdentifierExpression("b"),
                operator="*",
                right=IdentifierExpression("x"),
              ),
            ),
          ),
        ),
        parameter_names=("a", "b"),
        start_values=(0.5, 0.5),
        robust=True,
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, NlRegressionResult)
  assert robust.covariance == "robust"


def test_phase_15_nl_predict_supports_xb_and_residuals(tmp_path: Path) -> None:
  path = tmp_path / "nl.parquet"
  _write_nl_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      NlCommand(
        outcome="y",
        expression=FunctionCallExpression(
          name="exp",
          arguments=(
            BinaryExpression(
              left=IdentifierExpression("a"),
              operator="+",
              right=BinaryExpression(
                left=IdentifierExpression("b"),
                operator="*",
                right=IdentifierExpression("x"),
              ),
            ),
          ),
        ),
        parameter_names=("a", "b"),
        start_values=(0.5, 0.5),
      )
    )
    xb = executor.execute(PredictCommand(target_variable="y_hat", kind="xb"))
    residuals = executor.execute(PredictCommand(target_variable="u_hat", kind="residuals"))
    preview = executor.execute(HeadCommand(6))
  finally:
    executor.close()

  assert isinstance(xb, TransformResult)
  assert isinstance(residuals, TransformResult)
  assert isinstance(preview, PreviewResult)
  assert preview.rows[5][2] is None
  assert preview.rows[5][3] is None


def test_phase_15_nl_reports_prerequisite_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="nl requires an active dataset"):
      executor.execute(
        NlCommand(
          outcome="y",
          expression=IdentifierExpression("x"),
          parameter_names=("a",),
          start_values=(1.0,),
        )
      )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="nl unknown variable: y, x"):
      executor.execute(
        NlCommand(
          outcome="y",
          expression=BinaryExpression(
            left=IdentifierExpression("a"),
            operator="+",
            right=IdentifierExpression("x"),
          ),
          parameter_names=("a",),
          start_values=(1.0,),
        )
      )
  finally:
    executor.close()


def test_phase_15_nl_predict_supports_parameter_only_models(tmp_path: Path) -> None:
  path = tmp_path / "nl-constant.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0),
        (2.5),
        (4.0)
    ) as nl_data(y)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      NlCommand(
        outcome="y",
        expression=IdentifierExpression("a"),
        parameter_names=("a",),
        start_values=(2.0,),
      )
    )
    xb = executor.execute(PredictCommand(target_variable="y_hat", kind="xb"))
    residuals = executor.execute(PredictCommand(target_variable="u_hat", kind="residuals"))
    preview = executor.execute(HeadCommand(3))
  finally:
    executor.close()

  assert isinstance(xb, TransformResult)
  assert isinstance(residuals, TransformResult)
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("y", "y_hat", "u_hat")
  assert preview.rows == (
    (1.0, pytest.approx(2.5), pytest.approx(-1.5)),
    (2.5, pytest.approx(2.5), pytest.approx(0.0)),
    (4.0, pytest.approx(2.5), pytest.approx(1.5)),
  )


def test_phase_16_poisson_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "poisson.parquet"
  _write_poisson_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(PoissonCommand(outcome="y", predictors=("x", "z")))
  finally:
    executor.close()

  assert isinstance(result, PoissonRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.observation_count == 8
  assert result.log_likelihood is not None
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x", "z"]


def test_phase_16_poisson_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "poisson.parquet"
  _write_poisson_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(PoissonCommand(outcome="y", predictors=("x",), robust=True))
    clustered = executor.execute(
      PoissonCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id")
    )
  finally:
    executor.close()

  assert isinstance(robust, PoissonRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, PoissonRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_16_poisson_predict_and_estat_gof(tmp_path: Path) -> None:
  path = tmp_path / "poisson.parquet"
  _write_poisson_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PoissonCommand(outcome="y", predictors=("x", "z")))
    xb_predicted = executor.execute(PredictCommand(target_variable="xb_hat", kind="xb"))
    resid_predicted = executor.execute(PredictCommand(target_variable="u_hat", kind="residuals"))
    gof = executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()

  assert isinstance(xb_predicted, TransformResult)
  assert xb_predicted.message == "Predicted xb_hat"
  assert isinstance(resid_predicted, TransformResult)
  assert resid_predicted.message == "Predicted u_hat"
  assert isinstance(gof, TableResult)
  assert gof.headers == ("Metric", "Value")
  assert any(row[0] == "log_likelihood" for row in gof.rows)
  assert any(row[0] == "deviance" for row in gof.rows)


def test_phase_16_poisson_reports_prerequisite_errors(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  nonnegative_path = tmp_path / "negative-poisson.parquet"
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  _write_sql_parquet(
    nonnegative_path,
    """
    select * from (
      values
        (-1, 18.0),
        (1, 22.0)
    ) as poisson_data(y, x)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="poisson requires an active dataset"):
      executor.execute(PoissonCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="poisson unknown variable: y, x"):
      executor.execute(PoissonCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="poisson requires complete cluster values"):
      executor.execute(
        PoissonCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id")
      )
    executor.execute(UseCommand(nonnegative_path))
    with pytest.raises(ExecutionError, match="poisson outcome must be non-negative"):
      executor.execute(PoissonCommand(outcome="y", predictors=("x",)))
    with pytest.raises(
      ExecutionError,
      match="estat gof requires a prior poisson, nbreg, zip, or zinb model",
    ):
      executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()


def test_phase_16_nbreg_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "nbreg.parquet"
  _write_nbreg_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(NbregCommand(outcome="y", predictors=("x", "z")))
  finally:
    executor.close()

  assert isinstance(result, NbregRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.observation_count == 8
  assert result.log_likelihood is not None
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x", "z", "lnalpha"]


def test_phase_16_nbreg_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "nbreg.parquet"
  _write_nbreg_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(NbregCommand(outcome="y", predictors=("x",), robust=True))
    clustered = executor.execute(
      NbregCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id")
    )
  finally:
    executor.close()

  assert isinstance(robust, NbregRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, NbregRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_16_nbreg_predict_and_estat_gof(tmp_path: Path) -> None:
  path = tmp_path / "nbreg.parquet"
  _write_nbreg_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(NbregCommand(outcome="y", predictors=("x", "z")))
    xb_predicted = executor.execute(PredictCommand(target_variable="xb_hat", kind="xb"))
    resid_predicted = executor.execute(PredictCommand(target_variable="u_hat", kind="residuals"))
    gof = executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()

  assert isinstance(xb_predicted, TransformResult)
  assert xb_predicted.message == "Predicted xb_hat"
  assert isinstance(resid_predicted, TransformResult)
  assert resid_predicted.message == "Predicted u_hat"
  assert isinstance(gof, TableResult)
  assert gof.headers == ("Metric", "Value")
  assert any(row[0] == "log_likelihood" for row in gof.rows)
  assert any(row[0] == "pearson_chi2" for row in gof.rows)
  assert any(row[0] == "lnalpha" for row in gof.rows)


def test_phase_16_nbreg_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  nonnegative_path = tmp_path / "negative-nbreg.parquet"
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  _write_sql_parquet(
    nonnegative_path,
    """
    select * from (
      values
        (-1, 18.0),
        (1, 22.0)
    ) as nbreg_data(y, x)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="nbreg requires an active dataset"):
      executor.execute(NbregCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="nbreg unknown variable: y, x"):
      executor.execute(NbregCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="nbreg requires complete cluster values"):
      executor.execute(NbregCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id"))
    executor.execute(UseCommand(nonnegative_path))
    with pytest.raises(ExecutionError, match="nbreg outcome must be non-negative"):
      executor.execute(NbregCommand(outcome="y", predictors=("x",)))
    with pytest.raises(
      ExecutionError,
      match="estat gof requires a prior poisson, nbreg, zip, or zinb model",
    ):
      executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()


def test_phase_16_zip_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "zip.parquet"
  _write_zero_inflated_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      ZipCommand(outcome="y", predictors=("x", "z"), inflate_predictors=("zi",))
    )
  finally:
    executor.close()

  assert isinstance(result, ZipRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.inflate_predictors == ("zi",)
  assert result.observation_count == 8
  assert result.log_likelihood is None or isinstance(result.log_likelihood, float)


def test_phase_16_zip_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "zip.parquet"
  _write_zero_inflated_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      ZipCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",), robust=True)
    )
    clustered = executor.execute(
      ZipCommand(
        outcome="y",
        predictors=("x",),
        inflate_predictors=("zi",),
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, ZipRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, ZipRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_16_zip_predict_and_estat_gof(tmp_path: Path) -> None:
  path = tmp_path / "zip.parquet"
  _write_zero_inflated_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(ZipCommand(outcome="y", predictors=("x", "z"), inflate_predictors=("zi",)))
    xb_predicted = executor.execute(PredictCommand(target_variable="xb_hat", kind="xb"))
    resid_predicted = executor.execute(PredictCommand(target_variable="u_hat", kind="residuals"))
    gof = executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()

  assert isinstance(xb_predicted, TransformResult)
  assert xb_predicted.message == "Predicted xb_hat"
  assert isinstance(resid_predicted, TransformResult)
  assert resid_predicted.message == "Predicted u_hat"
  assert isinstance(gof, TableResult)
  assert gof.headers == ("Metric", "Value")
  assert any(row[0] == "log_likelihood" for row in gof.rows)
  assert any(row[0] == "pearson_chi2" for row in gof.rows)


def test_phase_16_zip_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  nonnegative_path = tmp_path / "negative-zip.parquet"
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  _write_sql_parquet(
    nonnegative_path,
    """
    select * from (
      values
        (-1, 18.0, 1.0),
        (1, 22.0, 2.0)
    ) as zip_data(y, x, zi)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="zip requires an active dataset"):
      executor.execute(ZipCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="zip unknown variable: y, x, zi"):
      executor.execute(ZipCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",)))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="zip requires complete cluster values"):
      executor.execute(
        ZipCommand(
          outcome="y",
          predictors=("x",),
          inflate_predictors=("x",),
          cluster_variable="cluster_id",
        )
      )
    executor.execute(UseCommand(nonnegative_path))
    with pytest.raises(ExecutionError, match="zip outcome must be non-negative"):
      executor.execute(ZipCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",)))
    with pytest.raises(
      ExecutionError,
      match="estat gof requires a prior poisson, nbreg, zip, or zinb model",
    ):
      executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()


def test_phase_16_zinb_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "zinb.parquet"
  _write_zero_inflated_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      ZinbCommand(outcome="y", predictors=("x", "z"), inflate_predictors=("zi",))
    )
  finally:
    executor.close()

  assert isinstance(result, ZinbRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.inflate_predictors == ("zi",)
  assert result.observation_count == 8
  assert result.log_likelihood is None or isinstance(result.log_likelihood, float)


def test_phase_16_zinb_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "zinb.parquet"
  _write_zero_inflated_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      ZinbCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",), robust=True)
    )
    clustered = executor.execute(
      ZinbCommand(
        outcome="y",
        predictors=("x",),
        inflate_predictors=("zi",),
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, ZinbRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, ZinbRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_16_zinb_predict_and_estat_gof(tmp_path: Path) -> None:
  path = tmp_path / "zinb.parquet"
  _write_zero_inflated_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(ZinbCommand(outcome="y", predictors=("x", "z"), inflate_predictors=("zi",)))
    xb_predicted = executor.execute(PredictCommand(target_variable="xb_hat", kind="xb"))
    resid_predicted = executor.execute(PredictCommand(target_variable="u_hat", kind="residuals"))
    gof = executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()

  assert isinstance(xb_predicted, TransformResult)
  assert xb_predicted.message == "Predicted xb_hat"
  assert isinstance(resid_predicted, TransformResult)
  assert resid_predicted.message == "Predicted u_hat"
  assert isinstance(gof, TableResult)
  assert gof.headers == ("Metric", "Value")
  assert any(row[0] == "log_likelihood" for row in gof.rows)
  assert any(row[0] == "lnalpha" for row in gof.rows)


def test_phase_16_zinb_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  nonnegative_path = tmp_path / "negative-zinb.parquet"
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  _write_sql_parquet(
    nonnegative_path,
    """
    select * from (
      values
        (-1, 18.0, 1.0),
        (1, 22.0, 2.0)
    ) as zinb_data(y, x, zi)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="zinb requires an active dataset"):
      executor.execute(ZinbCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="zinb unknown variable: y, x, zi"):
      executor.execute(ZinbCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",)))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="zinb requires complete cluster values"):
      executor.execute(
        ZinbCommand(
          outcome="y",
          predictors=("x",),
          inflate_predictors=("x",),
          cluster_variable="cluster_id",
        )
      )
    executor.execute(UseCommand(nonnegative_path))
    with pytest.raises(ExecutionError, match="zinb outcome must be non-negative"):
      executor.execute(ZinbCommand(outcome="y", predictors=("x",), inflate_predictors=("zi",)))
    with pytest.raises(
      ExecutionError,
      match="estat gof requires a prior poisson, nbreg, zip, or zinb model",
    ):
      executor.execute(EstatCommand(subcommand="gof"))
  finally:
    executor.close()


def test_phase_16_streg_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "streg.parquet"
  _write_streg_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      StregCommand(
        time_variable="time",
        predictors=("age", "income"),
        failure_variable="died",
        distribution="weibull",
      )
    )
  finally:
    executor.close()

  assert isinstance(result, StregRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.time_variable == "time"
  assert result.predictors == ("age", "income")
  assert result.failure_variable == "died"
  assert result.distribution == "weibull"
  assert result.observation_count == 8
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "age", "income"]


def test_phase_16_streg_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "streg.parquet"
  _write_streg_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    baseline = executor.execute(
      StregCommand(
        time_variable="time",
        predictors=("age",),
        failure_variable="died",
        distribution="exponential",
      )
    )
    robust = executor.execute(
      StregCommand(
        time_variable="time",
        predictors=("age",),
        failure_variable="died",
        distribution="exponential",
        robust=True,
      )
    )
    clustered = executor.execute(
      StregCommand(
        time_variable="time",
        predictors=("age",),
        failure_variable="died",
        distribution="weibull",
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(baseline, StregRegressionResult)
  assert isinstance(robust, StregRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, StregRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"
  assert robust.coefficients[0].standard_error != baseline.coefficients[0].standard_error
  assert clustered.coefficients[0].standard_error != baseline.coefficients[0].standard_error


def test_phase_16_streg_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  bad_event_path = tmp_path / "streg_bad_event.parquet"
  missing_cluster_path = tmp_path / "streg_missing_cluster.parquet"
  _write_sql_parquet(
    bad_event_path,
    """
    select * from (
      values
        (1.0, 2.0, 30.0),
        (2.0, 1.0, 35.0)
    ) as streg_data(time, died, age)
    """,
  )
  _write_sql_parquet(
    missing_cluster_path,
    """
    select * from (
      values
        (1.0, 1.0, 30.0, 'a'),
        (2.0, 0.0, 35.0, null),
        (3.0, 1.0, 40.0, 'b')
    ) as streg_data(time, died, age, cluster_id)
    """,
  )
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="streg requires an active dataset"):
      executor.execute(
        StregCommand(
          time_variable="time",
          predictors=("age",),
          failure_variable="died",
          distribution="weibull",
        )
      )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="streg unknown variable: time, died"):
      executor.execute(
        StregCommand(
          time_variable="time",
          predictors=("age",),
          failure_variable="died",
          distribution="weibull",
        )
      )
    executor.execute(UseCommand(bad_event_path))
    with pytest.raises(
      ExecutionError,
      match="streg failure variable must be binary with values 0 and 1",
    ):
      executor.execute(
        StregCommand(
          time_variable="time",
          predictors=("age",),
          failure_variable="died",
          distribution="weibull",
        )
      )
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="streg requires complete cluster values"):
      executor.execute(
        StregCommand(
          time_variable="time",
          predictors=("age",),
          failure_variable="died",
          distribution="weibull",
          cluster_variable="cluster_id",
        )
      )
  finally:
    executor.close()


def test_phase_15_logit_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "logit.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(LogitCommand(outcome="y", predictors=("x", "z")))
  finally:
    executor.close()

  assert isinstance(result, LogitRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.observation_count == 8
  assert result.pseudo_r_squared is not None
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x", "z"]


def test_phase_15_logit_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "logit.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(LogitCommand(outcome="y", predictors=("x",), robust=True))
    clustered = executor.execute(
      LogitCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id")
    )
  finally:
    executor.close()

  assert isinstance(robust, LogitRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, LogitRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_15_logit_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  nonbinary_path = tmp_path / "nonbinary.parquet"
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  _write_nonbinary_logit_parquet(nonbinary_path)
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="logit requires an active dataset"):
      executor.execute(LogitCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="logit unknown variable: y, x"):
      executor.execute(LogitCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(nonbinary_path))
    with pytest.raises(
      ExecutionError,
      match="logit outcome must be binary with values 0 and 1",
    ):
      executor.execute(LogitCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="logit requires complete cluster values"):
      executor.execute(LogitCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id"))
  finally:
    executor.close()


def test_phase_15_logit_clears_prior_regress_state(tmp_path: Path) -> None:
  path = tmp_path / "logit.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))
    executor.execute(LogitCommand(outcome="y", predictors=("x",)))
    predicted = executor.execute(PredictCommand(target_variable="y_hat_binary"))
    assert isinstance(predicted, TransformResult)
    with pytest.raises(ExecutionError, match="estat requires a prior regress model"):
      executor.execute(EstatCommand(subcommand="ovtest"))
  finally:
    executor.close()


def test_phase_15_probit_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "probit.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(ProbitCommand(outcome="y", predictors=("x", "z")))
  finally:
    executor.close()

  assert isinstance(result, ProbitRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.observation_count == 8
  assert result.pseudo_r_squared is not None
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x", "z"]


def test_phase_15_probit_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "probit.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(ProbitCommand(outcome="y", predictors=("x",), robust=True))
    clustered = executor.execute(
      ProbitCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id")
    )
  finally:
    executor.close()

  assert isinstance(robust, ProbitRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, ProbitRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_15_probit_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  nonbinary_path = tmp_path / "nonbinary.parquet"
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  _write_nonbinary_logit_parquet(nonbinary_path)
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="probit requires an active dataset"):
      executor.execute(ProbitCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="probit unknown variable: y, x"):
      executor.execute(ProbitCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(nonbinary_path))
    with pytest.raises(
      ExecutionError,
      match="probit outcome must be binary with values 0 and 1",
    ):
      executor.execute(ProbitCommand(outcome="y", predictors=("x",)))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="probit requires complete cluster values"):
      executor.execute(ProbitCommand(outcome="y", predictors=("x",), cluster_variable="cluster_id"))
  finally:
    executor.close()


def test_phase_15_estat_margins_after_logit_and_probit(tmp_path: Path) -> None:
  path = tmp_path / "binary.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(LogitCommand(outcome="y", predictors=("x", "z")))
    logit_margins = executor.execute(EstatCommand(subcommand="margins"))
    executor.execute(ProbitCommand(outcome="y", predictors=("x", "z")))
    probit_margins = executor.execute(EstatCommand(subcommand="margins"))
  finally:
    executor.close()

  assert isinstance(logit_margins, TableResult)
  assert logit_margins.headers == ("Variable", "Metric", "Value")
  assert any(row[0] == "x" and row[1] == "dy_dx" for row in logit_margins.rows)
  assert any(row[0] == "z" and row[1] == "ci_upper" for row in logit_margins.rows)
  assert isinstance(probit_margins, TableResult)
  assert probit_margins.headers == ("Variable", "Metric", "Value")
  assert any(row[0] == "x" and row[1] == "dy_dx" for row in probit_margins.rows)
  assert any(row[0] == "z" and row[1] == "ci_upper" for row in probit_margins.rows)


def test_phase_15_estat_margins_requires_prior_binary_model(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(
      ExecutionError,
      match="estat margins requires a prior logit or probit model",
    ):
      executor.execute(EstatCommand(subcommand="margins"))
  finally:
    executor.close()


def test_phase_15_predict_supports_binary_xb_and_pr(tmp_path: Path) -> None:
  path = tmp_path / "binary.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(LogitCommand(outcome="y", predictors=("x", "z")))
    xb_predicted = executor.execute(PredictCommand(target_variable="xb_hat", kind="xb"))
    pr_predicted = executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
  finally:
    executor.close()

  assert isinstance(xb_predicted, TransformResult)
  assert xb_predicted.message == "Predicted xb_hat"
  assert isinstance(pr_predicted, TransformResult)
  assert pr_predicted.message == "Predicted pr_hat"
  assert [column.name for column in pr_predicted.dataset.columns] == [
    "y",
    "x",
    "z",
    "cluster_id",
    "xb_hat",
    "pr_hat",
  ]


def test_phase_15_predict_binary_preserves_missing_rows_as_null(tmp_path: Path) -> None:
  path = tmp_path / "binary-missing.parquet"
  _write_binary_missing_predictor_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(LogitCommand(outcome="y", predictors=("x", "z")))
    executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
    preview = executor.execute(HeadCommand(limit=4))
  finally:
    executor.close()

  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("y", "x", "z", "pr_hat")
  assert preview.rows[1][3] is None


def test_phase_15_predict_reports_binary_routing_errors(
  tmp_path: Path,
  sample_parquet: Path,
) -> None:
  path = tmp_path / "binary.parquet"
  _write_logit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(LogitCommand(outcome="y", predictors=("x", "z")))
    with pytest.raises(
      ExecutionError,
      match="predict residuals is not available after logit or probit",
    ):
      executor.execute(PredictCommand(target_variable="y_resid", kind="residuals"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(
      ExecutionError,
      match="predict option pr requires a prior logit or probit model",
    ):
      executor.execute(PredictCommand(target_variable="pr_hat", kind="pr"))
  finally:
    executor.close()


def test_phase_15_tobit_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "tobit.parquet"
  _write_tobit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      TobitCommand(
        outcome="y",
        predictors=("x", "z"),
        lower_limit=0.0,
        upper_limit=10.0,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, TobitRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x", "z")
  assert result.observation_count == 8
  assert [estimate.name for estimate in result.coefficients] == ["intercept", "x", "z"]


def test_phase_15_tobit_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "tobit.parquet"
  _write_tobit_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      TobitCommand(outcome="y", predictors=("x",), lower_limit=0.0, robust=True)
    )
    clustered = executor.execute(
      TobitCommand(
        outcome="y",
        predictors=("x",),
        lower_limit=0.0,
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, TobitRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, TobitRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_15_tobit_handles_internal_name_collisions(tmp_path: Path) -> None:
  path = tmp_path / "tobit-collision.parquet"
  _write_tobit_internal_name_collision_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      TobitCommand(outcome="y", predictors=("tabdat_left", "tabdat_right"), lower_limit=0.0)
    )
  finally:
    executor.close()

  assert isinstance(result, TobitRegressionResult)
  assert result.predictors == ("tabdat_left", "tabdat_right")


def test_phase_15_tobit_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  _write_missing_cluster_logit_parquet(missing_cluster_path)
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="tobit requires an active dataset"):
      executor.execute(TobitCommand(outcome="y", predictors=("x",), lower_limit=0.0))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="tobit unknown variable: y, x"):
      executor.execute(TobitCommand(outcome="y", predictors=("x",), lower_limit=0.0))
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="tobit requires complete cluster values"):
      executor.execute(
        TobitCommand(
          outcome="y",
          predictors=("x",),
          lower_limit=0.0,
          cluster_variable="cluster_id",
        )
      )
    with pytest.raises(ExecutionError, match="tobit lower limit must be less than upper limit"):
      executor.execute(
        TobitCommand(outcome="y", predictors=("x",), lower_limit=1.0, upper_limit=1.0)
      )
  finally:
    executor.close()


def test_phase_15_heckman_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "heckman.parquet"
  _write_heckman_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      HeckmanCommand(
        outcome="y",
        predictors=("x",),
        selection_dependent="s",
        selection_predictors=("z",),
      )
    )
  finally:
    executor.close()

  assert isinstance(result, HeckmanRegressionResult)
  assert result.covariance == "nonrobust"
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.selection_dependent == "s"
  assert result.selection_predictors == ("z",)
  assert result.observation_count == 8
  assert [estimate.name for estimate in result.outcome_coefficients] == [
    "intercept",
    "x",
    "mills_lambda",
  ]
  assert [estimate.name for estimate in result.selection_coefficients] == ["intercept", "z"]


def test_phase_15_heckman_supports_covariance_modes(tmp_path: Path) -> None:
  path = tmp_path / "heckman.parquet"
  _write_heckman_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      HeckmanCommand(
        outcome="y",
        predictors=("x",),
        selection_dependent="s",
        selection_predictors=("z",),
        robust=True,
      )
    )
    clustered = executor.execute(
      HeckmanCommand(
        outcome="y",
        predictors=("x",),
        selection_dependent="s",
        selection_predictors=("z",),
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, HeckmanRegressionResult)
  assert robust.covariance == "robust"
  assert isinstance(clustered, HeckmanRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_15_heckman_noconstant_labels_coefficients(tmp_path: Path) -> None:
  path = tmp_path / "heckman.parquet"
  _write_heckman_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      HeckmanCommand(
        outcome="y",
        predictors=("x",),
        selection_dependent="s",
        selection_predictors=("z",),
        include_intercept=False,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, HeckmanRegressionResult)
  assert [estimate.name for estimate in result.outcome_coefficients] == ["x", "mills_lambda"]
  assert [estimate.name for estimate in result.selection_coefficients] == ["z"]


def test_phase_15_heckman_reports_prerequisite_errors(sample_parquet: Path, tmp_path: Path) -> None:
  path = tmp_path / "heckman.parquet"
  missing_cluster_path = tmp_path / "missing-cluster.parquet"
  _write_heckman_parquet(path)
  _write_missing_cluster_heckman_parquet(missing_cluster_path)
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="heckman requires an active dataset"):
      executor.execute(
        HeckmanCommand(
          outcome="y",
          predictors=("x",),
          selection_dependent="s",
          selection_predictors=("z",),
        )
      )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="heckman unknown variable: y, x, s, z"):
      executor.execute(
        HeckmanCommand(
          outcome="y",
          predictors=("x",),
          selection_dependent="s",
          selection_predictors=("z",),
        )
      )
    executor.execute(UseCommand(missing_cluster_path))
    with pytest.raises(ExecutionError, match="heckman requires complete cluster values"):
      executor.execute(
        HeckmanCommand(
          outcome="y",
          predictors=("x",),
          selection_dependent="s",
          selection_predictors=("z",),
          cluster_variable="cluster_id",
        )
      )
  finally:
    executor.close()


def test_phase_15_heckman_predict_state_invalidation(tmp_path: Path) -> None:
  path = tmp_path / "heckman.parquet"
  _write_heckman_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      HeckmanCommand(
        outcome="y",
        predictors=("x",),
        selection_dependent="s",
        selection_predictors=("z",),
      )
    )
    assert executor.state.heckman_regression is not None
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))
    assert executor.state.heckman_regression is None
  finally:
    executor.close()


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
    with pytest.raises(
      ExecutionError,
      match=(
        "predict requires a prior regress, lasso, ridge, elasticnet, bayes, spregress, qreg, "
        "did, cfregress, nl, poisson, nbreg, zip, or zinb model"
      ),
    ):
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
    with pytest.raises(
      ExecutionError,
      match="estat residuals requires a prior regress or qreg model",
    ):
      executor.execute(EstatCommand(subcommand="residuals"))
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


def test_phase_14_ivregress_gmm_returns_typed_result_and_overid(tmp_path: Path) -> None:
  path = tmp_path / "iv-overid.parquet"
  _write_iv_overid_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    gmm = executor.execute(
      IvRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst", "z_inst2"),
        estimator="gmm",
      )
    )
    overid = executor.execute(EstatCommand(subcommand="overid"))
  finally:
    executor.close()

  assert isinstance(gmm, IvRegressionResult)
  assert gmm.estimator == "gmm"
  assert gmm.covariance == "nonrobust"
  assert isinstance(overid, TableResult)
  assert overid.headers == ("Test", "Metric", "Value")
  assert any(row[0] == "gmm_j" for row in overid.rows)
  assert not any(row[0] == "sargan" for row in overid.rows)


def test_phase_14_cfregress_returns_typed_result_and_covariance(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    robust = executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
        robust=True,
      )
    )
    clustered = executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
        cluster_variable="cluster_id",
      )
    )
  finally:
    executor.close()

  assert isinstance(robust, CfRegressionResult)
  assert robust.covariance == "robust"
  assert robust.outcome == "y"
  assert robust.exogenous == ("w",)
  assert robust.endogenous == "x_endog"
  assert robust.instruments == ("z_inst",)
  assert robust.observation_count == 8
  assert [estimate.name for estimate in robust.coefficients] == [
    "intercept",
    "w",
    "x_endog",
    "cf_residual",
  ]
  assert isinstance(clustered, CfRegressionResult)
  assert clustered.covariance == "cluster(cluster_id)"


def test_phase_14_cfregress_reports_prerequisite_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="cfregress requires an active dataset"):
      executor.execute(
        CfRegressCommand(
          outcome="y",
          exogenous=("w",),
          endogenous="x_endog",
          instruments=("z_inst",),
        )
      )
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(
      UnknownVariableError,
      match="cfregress unknown variable: w, x_endog, z_inst",
    ):
      executor.execute(
        CfRegressCommand(
          outcome="cost",
          exogenous=("w",),
          endogenous="x_endog",
          instruments=("z_inst",),
        )
      )
  finally:
    executor.close()


def test_phase_14_predict_works_after_cfregress(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    predicted = executor.execute(PredictCommand(target_variable="y_hat_cf"))
    residuals = executor.execute(PredictCommand(target_variable="y_resid_cf", kind="residuals"))
    preview = executor.execute(HeadCommand(1))
  finally:
    executor.close()

  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted y_hat_cf"
  assert isinstance(residuals, TransformResult)
  assert residuals.message == "Predicted y_resid_cf"
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("w", "y", "x_endog", "z_inst", "cluster_id", "y_hat_cf", "y_resid_cf")


def test_phase_14_predict_after_cfregress_handles_cf_residual_name_collision(
  tmp_path: Path,
) -> None:
  path = tmp_path / "cf-name-collision.parquet"
  _write_cfresidual_name_collision_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("cf_residual",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    executor.execute(PredictCommand(target_variable="y_hat_cf"))
    preview = executor.execute(HeadCommand(2))
  finally:
    executor.close()

  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("cf_residual", "x_endog", "z_inst", "y", "y_hat_cf")
  assert preview.rows[0][4] != pytest.approx(preview.rows[1][4])
  assert preview.rows[0][4] == pytest.approx(8.0, rel=1e-5, abs=1e-5)
  assert preview.rows[1][4] == pytest.approx(10.0, rel=1e-5, abs=1e-5)


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
    with pytest.raises(
      ExecutionError,
      match=(
        "predict requires a prior regress, lasso, ridge, elasticnet, bayes, spregress, qreg, "
        "did, cfregress, nl, poisson, nbreg, zip, or zinb model"
      ),
    ):
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


def test_phase_14_estat_endogenous_after_ivregress_2sls(tmp_path: Path) -> None:
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
    endogenous = executor.execute(EstatCommand(subcommand="endogenous"))
  finally:
    executor.close()

  assert isinstance(endogenous, TableResult)
  assert endogenous.headers == ("Test", "Metric", "Value")
  assert any(row[0] == "durbin" for row in endogenous.rows)
  assert any(row[0] == "wu_hausman" for row in endogenous.rows)


def test_phase_14_estat_endogenous_rejects_non_2sls_ivregress(tmp_path: Path) -> None:
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
        estimator="gmm",
      )
    )
    with pytest.raises(
      ExecutionError,
      match="estat endogenous requires a prior ivregress 2sls model",
    ):
      executor.execute(EstatCommand(subcommand="endogenous"))
  finally:
    executor.close()


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
    with pytest.raises(
      ExecutionError,
      match="estat overid requires a prior ivregress or xtabond model",
    ):
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


def test_phase_14_xtreg_clears_prior_did_state(tmp_path: Path) -> None:
  path = tmp_path / "did.parquet"
  _write_did_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(
      DidCommand(
        outcome="wage",
        controls=("exposure",),
        treatment_variable="treated",
        post_variable="post",
      )
    )
    executor.execute(
      XtRegCommand(
        outcome="wage",
        predictors=("exposure",),
        estimator="fe",
      )
    )
    with pytest.raises(
      ExecutionError,
      match=(
        "predict requires a prior regress, lasso, ridge, elasticnet, bayes, spregress, qreg, "
        "did, cfregress, nl, poisson, nbreg, zip, or zinb model"
      ),
    ):
      executor.execute(PredictCommand(target_variable="pred_after_xtreg"))
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


def test_phase_14_estat_endogenous_after_cfregress(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    endogenous = executor.execute(EstatCommand(subcommand="endogenous"))
  finally:
    executor.close()

  assert isinstance(endogenous, TableResult)
  assert endogenous.headers == ("Test", "Metric", "Value")
  assert endogenous.rows[0] == ("control_function_residual", "test", "cf_residual")
  assert endogenous.rows[1][0] == "control_function_residual"
  assert endogenous.rows[1][1] == "estimate"
  assert isinstance(endogenous.rows[1][2], float)
  assert endogenous.rows[2][0] == "control_function_residual"
  assert endogenous.rows[2][1] == "std_error"
  assert isinstance(endogenous.rows[2][2], float)
  assert endogenous.rows[3][0] == "control_function_residual"
  assert endogenous.rows[3][1] == "statistic"
  assert isinstance(endogenous.rows[3][2], float)
  assert endogenous.rows[4][0] == "control_function_residual"
  assert endogenous.rows[4][1] == "p_value"
  assert isinstance(endogenous.rows[4][2], float)
  assert endogenous.rows[5] == ("control_function_residual", "ci_level", 95.0)
  assert endogenous.rows[6][0] == "control_function_residual"
  assert endogenous.rows[6][1] == "ci_lower"
  assert isinstance(endogenous.rows[6][2], float)
  assert endogenous.rows[7][0] == "control_function_residual"
  assert endogenous.rows[7][1] == "ci_upper"
  assert isinstance(endogenous.rows[7][2], float)
  assert endogenous.rows[8][0] == "control_function_residual"
  assert endogenous.rows[8][1] == "distribution"
  assert endogenous.rows[8][2] in {"t", "normal"}
  assert endogenous.rows[9][0] == "control_function_residual"
  assert endogenous.rows[9][1] == "df"
  assert isinstance(endogenous.rows[9][2], (float, str))


def test_phase_17_did_returns_typed_result_and_predicts_xb(tmp_path: Path) -> None:
  path = tmp_path / "did.parquet"
  _write_did_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    result = executor.execute(
      DidCommand(
        outcome="wage",
        controls=("exposure",),
        treatment_variable="treated",
        post_variable="post",
        robust=True,
      )
    )
    predicted = executor.execute(PredictCommand(target_variable="did_xb", kind="xb"))
    preview = executor.execute(HeadCommand(2))
  finally:
    executor.close()

  assert isinstance(result, DidRegressionResult)
  assert result.covariance == "robust"
  assert result.outcome == "wage"
  assert result.controls == ("exposure",)
  assert result.treatment_variable == "treated"
  assert result.post_variable == "post"
  assert result.observation_count == 8
  assert isinstance(predicted, TransformResult)
  assert predicted.message == "Predicted did_xb"
  assert isinstance(preview, PreviewResult)
  assert "did_xb" in preview.columns


def test_phase_17_xtabond_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "xtabond.parquet"
  _write_xtabond_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    result = executor.execute(
      XtAbondCommand(
        outcome="wage",
        predictors=("exper",),
        robust=True,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, XtAbondRegressionResult)
  assert result.covariance == "robust"
  assert result.outcome == "wage"
  assert result.predictors == ("exper",)
  assert result.observation_count > 0
  assert result.coefficient_count == 2
  assert len(result.coefficients) == 2


def test_phase_17_xtabond_supports_lag_and_instrument_options(tmp_path: Path) -> None:
  path = tmp_path / "xtabond-lagged.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2019, 9.0, 0.5),
        (1, 2020, 10.0, 1.0),
        (1, 2021, 13.0, 2.0),
        (1, 2022, 15.0, 4.0),
        (2, 2019, 6.0, 0.0),
        (2, 2020, 7.0, 0.0),
        (2, 2021, 9.0, 1.0),
        (2, 2022, 12.0, 1.5),
        (3, 2019, 18.0, 2.5),
        (3, 2020, 20.0, 3.0),
        (3, 2021, 19.0, 2.0),
        (3, 2022, 21.0, 3.0)
    ) as panel_data(firm_id, year, wage, exper)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    result = executor.execute(
      XtAbondCommand(
        outcome="wage",
        predictors=("exper",),
        lag_depth=2,
        instrument_lag_start=3,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, XtAbondRegressionResult)
  assert result.coefficient_count == 2
  assert result.coefficients[-1].name == "L2.wage"


def test_phase_17_xtabond_requires_panel_metadata(tmp_path: Path) -> None:
  path = tmp_path / "xtabond.parquet"
  _write_xtabond_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(
      ExecutionError,
      match="xtabond requires panel metadata; run panel <id_var> <time_var> first",
    ):
      executor.execute(XtAbondCommand(outcome="wage", predictors=("exper",)))
  finally:
    executor.close()


def test_phase_17_xtabond_requires_complete_dynamic_panel_sample(tmp_path: Path) -> None:
  path = tmp_path / "xtabond-short.parquet"
  _write_xtabond_short_panel_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    with pytest.raises(ExecutionError, match="xtabond requires at least one complete observation"):
      executor.execute(XtAbondCommand(outcome="wage", predictors=("exposure",)))
  finally:
    executor.close()


def test_phase_17_xtabond_r_fallback_runs_when_python_fit_fails(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  path = tmp_path / "xtabond.parquet"
  _write_xtabond_parquet(path)
  monkeypatch.setattr(
    "tabdat.executor._fit_xtabond_python",
    lambda **_: (_ for _ in ()).throw(ExecutionError("xtabond failed")),
  )
  monkeypatch.setattr(
    "tabdat.executor._fit_xtabond_r_fallback",
    lambda **_: executor_module._XtAbondFitResult(
      covariance="nonrobust",
      coefficients=(
        CoefficientEstimate(name="exper", value=1.0),
        CoefficientEstimate(name="L1.wage", value=0.5),
      ),
      fitted_model=object(),
    ),
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    result = executor.execute(XtAbondCommand(outcome="wage", predictors=("exper",)))
  finally:
    executor.close()

  assert isinstance(result, XtAbondRegressionResult)
  assert result.covariance == "nonrobust"


def test_phase_17_estat_overid_supports_xtabond(tmp_path: Path) -> None:
  path = tmp_path / "xtabond-overid.parquet"
  _write_xtabond_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(XtAbondCommand(outcome="wage", predictors=("exper",), robust=True))
    result = executor.execute(EstatCommand(subcommand="overid"))
  finally:
    executor.close()

  assert isinstance(result, TableResult)
  assert result.headers == ("Test", "Metric", "Value")
  assert any(row[0] == "gmm_j" for row in result.rows)


def test_phase_17_predict_supports_xtabond_xb_and_residuals(tmp_path: Path) -> None:
  path = tmp_path / "xtabond-predict.parquet"
  _write_xtabond_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(XtAbondCommand(outcome="wage", predictors=("exper",), robust=True))
    xb = executor.execute(PredictCommand(target_variable="xtabond_xb", kind="xb"))
    resid = executor.execute(PredictCommand(target_variable="xtabond_resid", kind="residuals"))
    preview = executor.execute(HeadCommand(8))
  finally:
    executor.close()

  assert isinstance(xb, TransformResult)
  assert xb.message == "Predicted xtabond_xb"
  assert isinstance(resid, TransformResult)
  assert resid.message == "Predicted xtabond_resid"
  assert isinstance(preview, PreviewResult)
  assert "xtabond_xb" in preview.columns
  assert "xtabond_resid" in preview.columns


def test_phase_17_predict_xtabond_requires_matching_panel_metadata(tmp_path: Path) -> None:
  path = tmp_path / "xtabond-metadata.parquet"
  _write_xtabond_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(XtAbondCommand(outcome="wage", predictors=("exper",)))
    executor.execute(PanelCommand(action="clear"))
    with pytest.raises(
      ExecutionError,
      match="predict requires a prior xtabond model with matching panel metadata",
    ):
      executor.execute(PredictCommand(target_variable="xtabond_xb", kind="xb"))
  finally:
    executor.close()


def test_phase_17_predict_xtabond_rejects_pr(tmp_path: Path) -> None:
  path = tmp_path / "xtabond-pr.parquet"
  _write_xtabond_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(XtAbondCommand(outcome="wage", predictors=("exper",)))
    with pytest.raises(ExecutionError, match="predict option pr is not available after xtabond"):
      executor.execute(PredictCommand(target_variable="xtabond_pr", kind="pr"))
  finally:
    executor.close()


def test_phase_17_xtabond_sample_orders_numeric_time_values() -> None:
  rows: tuple[tuple[object, ...], ...] = (
    (1, 1, 10.0, 0.0),
    (1, 10, 16.0, 2.0),
    (1, 2, 12.0, 1.0),
  )
  sample = _xtabond_sample(
    rows=rows,
    predictor_count=1,
    lag_depth=1,
    instrument_lag_start=2,
  )

  assert sample is not None
  dependent, exogenous, endogenous, instruments = sample
  assert dependent == (4.0,)
  assert exogenous == ((1.0,),)
  assert endogenous == (2.0,)
  assert instruments == ((10.0,),)


def test_phase_17_xtlogit_returns_typed_result(tmp_path: Path) -> None:
  path = tmp_path / "xtlogit.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 0, 0.3, 1.0),
        (1, 2021, 1, 0.8, 1.2),
        (1, 2022, 1, 1.1, 1.4),
        (2, 2020, 0, 0.2, 0.9),
        (2, 2021, 0, 0.4, 1.0),
        (2, 2022, 1, 0.9, 1.3),
        (3, 2020, 0, 0.1, 0.8),
        (3, 2021, 1, 0.9, 1.1),
        (3, 2022, 1, 1.2, 1.5)
    ) as panel_data(firm_id, year, promoted, training, tenure)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    result = executor.execute(
      XtLogitCommand(
        outcome="promoted",
        predictors=("training", "tenure"),
        robust=True,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, XtLogitRegressionResult)
  assert result.outcome == "promoted"
  assert result.predictors == ("training", "tenure")
  assert result.covariance == "robust"
  assert result.observation_count > 0


def test_phase_17_xtlogit_robust_passes_cov_type(
  monkeypatch: pytest.MonkeyPatch,
  tmp_path: Path,
) -> None:
  path = tmp_path / "xtlogit-robust.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 0, 0.3, 1.0),
        (1, 2021, 1, 0.8, 1.2),
        (2, 2020, 0, 0.2, 0.9),
        (2, 2021, 1, 0.9, 1.3)
    ) as panel_data(firm_id, year, promoted, training, tenure)
    """,
  )
  seen_cov_type: dict[str, str | None] = {"value": None}
  original_fit = cast(Any, executor_module.ConditionalLogit.fit)

  def _fit_with_capture(self: Any, *args: Any, **kwargs: Any) -> Any:
    cov_type = kwargs.get("cov_type")
    seen_cov_type["value"] = str(cov_type) if cov_type is not None else None
    return original_fit(self, *args, **kwargs)

  monkeypatch.setattr(executor_module.ConditionalLogit, "fit", _fit_with_capture)

  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(
      XtLogitCommand(
        outcome="promoted",
        predictors=("training", "tenure"),
        robust=True,
      )
    )
  finally:
    executor.close()

  assert seen_cov_type["value"] == "robust"


def test_phase_17_xtlogit_requires_panel_metadata(tmp_path: Path) -> None:
  path = tmp_path / "xtlogit-no-panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 0, 0.3),
        (1, 2021, 1, 0.8)
    ) as panel_data(firm_id, year, promoted, training)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(
      ExecutionError,
      match="xtlogit requires panel metadata; run panel <id_var> <time_var> first",
    ):
      executor.execute(XtLogitCommand(outcome="promoted", predictors=("training",)))
  finally:
    executor.close()


def test_phase_17_lowess_generates_column(tmp_path: Path) -> None:
  path = tmp_path / "lowess.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 1.0),
        (2.0, 2.0),
        (3.0, 3.0),
        (4.0, 4.0),
        (5.0, 5.0)
    ) as lowess_data(wage, exper)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      LowessCommand(
        outcome="wage",
        predictor="exper",
        target_variable="wage_lowess",
        bandwidth=0.5,
      )
    )
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.message == "Generated wage_lowess with lowess"
  assert isinstance(preview, PreviewResult)
  assert "wage_lowess" in preview.columns


def test_phase_17_lowess_preserves_panel_metadata(tmp_path: Path) -> None:
  path = tmp_path / "lowess-panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 1.0, 1.0),
        (1, 2021, 2.0, 2.0),
        (2, 2020, 3.0, 3.0),
        (2, 2021, 4.0, 4.0)
    ) as lowess_data(firm_id, year, wage, exper)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(
      LowessCommand(
        outcome="wage",
        predictor="exper",
        target_variable="wage_lowess",
        bandwidth=0.5,
      )
    )
    panel_report = executor.execute(PanelCommand(action="report"))
  finally:
    executor.close()

  assert isinstance(panel_report, PanelResult)
  assert panel_report.metadata == PanelMetadata(id_variable="firm_id", time_variable="year")


def test_phase_17_did_requires_panel_metadata(tmp_path: Path) -> None:
  path = tmp_path / "did.parquet"
  _write_did_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(
      ExecutionError,
      match="did requires panel metadata; run panel <id_var> <time_var> first",
    ):
      executor.execute(
        DidCommand(
          outcome="wage",
          controls=("exposure",),
          treatment_variable="treated",
          post_variable="post",
        )
      )
  finally:
    executor.close()


def test_phase_17_did_requires_binary_treatment_and_post(tmp_path: Path) -> None:
  path = tmp_path / "did-nonbinary.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 0, 0, 1.0),
        (1, 2021, 11.0, 2, 1, 1.1),
        (2, 2020, 9.5, 0, 0, 0.9),
        (2, 2021, 10.8, 1, 1, 1.0)
    ) as did_data(firm_id, year, wage, treated, post, exposure)
    """,
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    with pytest.raises(
      ExecutionError,
      match="did treatment and post variables must be binary with values 0 and 1",
    ):
      executor.execute(
        DidCommand(
          outcome="wage",
          controls=("exposure",),
          treatment_variable="treated",
          post_variable="post",
        )
      )
  finally:
    executor.close()


def test_phase_17_estat_did_reports_interaction_diagnostics(tmp_path: Path) -> None:
  path = tmp_path / "did.parquet"
  _write_did_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(PanelCommand(action="set", id_variable="firm_id", time_variable="year"))
    executor.execute(
      DidCommand(
        outcome="wage",
        controls=("exposure",),
        treatment_variable="treated",
        post_variable="post",
      )
    )
    result = executor.execute(EstatCommand(subcommand="did"))
  finally:
    executor.close()

  assert isinstance(result, TableResult)
  assert result.headers == ("Test", "Metric", "Value")
  observed = {str(row[1]): row[2] for row in result.rows}
  assert result.rows[0][0] == "did_interaction"
  assert observed["coefficient"] is not None
  assert observed["treated_post_count"] == 2.0
  assert observed["treated_pre_count"] == 2.0
  assert observed["untreated_post_count"] == 2.0
  assert observed["untreated_pre_count"] == 2.0
  assert isinstance(observed["raw_diff_in_diff"], float)


def test_phase_17_estat_did_requires_prior_did(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="estat did requires a prior did model"):
      executor.execute(EstatCommand(subcommand="did"))
  finally:
    executor.close()


def test_phase_14_estat_endogenous_uses_residual_inclusion_slot_with_name_collision(
  tmp_path: Path,
) -> None:
  path = tmp_path / "cf-name-collision.parquet"
  _write_cfresidual_name_collision_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    fit = executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("cf_residual",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    endogenous = executor.execute(EstatCommand(subcommand="endogenous"))
  finally:
    executor.close()

  assert isinstance(fit, CfRegressionResult)
  assert isinstance(endogenous, TableResult)
  expected_residual = fit.coefficients[-1]
  assert expected_residual.name == "cf_residual"
  observed = {row[1]: row[2] for row in endogenous.rows}
  assert observed["test"] == "cf_residual"
  assert observed["estimate"] == pytest.approx(expected_residual.value)
  assert observed["std_error"] == pytest.approx(expected_residual.standard_error)
  assert observed["statistic"] == pytest.approx(expected_residual.statistic)
  assert observed["p_value"] == pytest.approx(expected_residual.p_value)
  assert observed["ci_level"] == 95.0
  assert isinstance(observed["ci_lower"], float)
  assert isinstance(observed["ci_upper"], float)
  assert observed["distribution"] in {"t", "normal"}
  assert isinstance(observed["df"], (float, str))


def test_phase_14_estat_firststage_after_cfregress(tmp_path: Path) -> None:
  path = tmp_path / "iv-regression.parquet"
  _write_iv_regression_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      CfRegressCommand(
        outcome="y",
        exogenous=("w",),
        endogenous="x_endog",
        instruments=("z_inst",),
      )
    )
    firststage = executor.execute(EstatCommand(subcommand="firststage"))
  finally:
    executor.close()

  assert isinstance(firststage, TableResult)
  assert firststage.headers == ("Variable", "Metric", "Value")
  observed = {(str(row[0]), str(row[1])): row[2] for row in firststage.rows}
  assert ("intercept", "coefficient") in observed
  assert ("w", "coefficient") in observed
  assert ("z_inst", "coefficient") in observed
  assert ("first_stage", "observation_count") in observed
  assert observed[("first_stage", "observation_count")] == 8
  assert ("first_stage", "r_squared") in observed
  assert isinstance(observed[("first_stage", "r_squared")], float)


def test_phase_14_estat_endogenous_requires_prior_cfregress(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="estat endogenous requires a prior cfregress model"):
      executor.execute(EstatCommand(subcommand="endogenous"))
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
    with pytest.raises(
      ExecutionError,
      match=(
        "predict requires a prior regress, lasso, ridge, elasticnet, bayes, spregress, qreg, "
        "did, cfregress, nl, poisson, nbreg, zip, or zinb model"
      ),
    ):
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
  assert report_after == PanelResult(
    "report",
    PanelMetadata("firm_id", "year"),
    summary=PanelStructureSummary(
      observation_count=3,
      entity_count=2,
      time_count=2,
      min_observations_per_entity=1,
      max_observations_per_entity=2,
    ),
  )
  assert cleared == PanelResult(action="report")
  assert restored == PanelResult(
    "report",
    PanelMetadata("firm_id", "year"),
    summary=PanelStructureSummary(
      observation_count=3,
      entity_count=2,
      time_count=2,
      min_observations_per_entity=1,
      max_observations_per_entity=2,
    ),
  )


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

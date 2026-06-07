from pathlib import Path

import duckdb
import pytest

from tabdat.errors import ExecutionError, ParseError
from tabdat.executor import Executor
from tabdat.help import available_help_topics, load_help_topic
from tabdat.models import (
  PredictCommand,
  SpatialRegressionResult,
  SpregressCommand,
  UseCommand,
)
from tabdat.parser import parse_command
from tabdat.shell import COMMAND_NAMES, _option_completions


def _write_sql_parquet(path: Path, query: str) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(f"copy ({query}) to ? (format parquet)", [str(path)])
  finally:
    connection.close()


def _write_spatial_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (10.0, 1.0, 1.0, 1.0),
        (12.0, 2.0, 1.5, 2.0),
        (15.0, 3.0, 2.0, 1.5),
        (18.0, 4.0, 2.5, 3.0),
        (20.0, 5.0, 3.0, 2.5),
        (22.0, 6.0, 3.5, 3.5),
        (25.0, 7.0, 4.0, 4.0),
        (28.0, 8.0, 4.5, 4.5)
    ) as sp_data(y, x, lat, lon)
    """,
  )


def test_parse_spregress_command() -> None:
  # Default model(lag) and default knn(5)
  assert parse_command("spregress y x1 x2, coord(lat lon)") == SpregressCommand(
    outcome="y",
    predictors=("x1", "x2"),
    model_type="lag",
    coord_variables=("lat", "lon"),
    knn=5,
    robust=False,
  )

  # Custom model, knn, robust
  assert parse_command(
    "spregress y x, coord(lat lon) model(error) knn(3) robust"
  ) == SpregressCommand(
    outcome="y",
    predictors=("x",),
    model_type="error",
    coord_variables=("lat", "lon"),
    knn=3,
    robust=True,
  )


def test_parse_spregress_errors() -> None:
  # Missing coord option
  with pytest.raises(ParseError, match="spregress option coord expects exactly two variables"):
    parse_command("spregress y x")

  # coord with 1 variable
  with pytest.raises(ParseError, match="spregress option coord expects exactly two variables"):
    parse_command("spregress y x, coord(lat)")

  # coord with 3 variables
  with pytest.raises(ParseError, match="spregress option coord expects exactly two variables"):
    parse_command("spregress y x, coord(lat lon alt)")

  # Invalid model type
  with pytest.raises(ParseError, match="spregress option model must be 'lag' or 'error'"):
    parse_command("spregress y x, coord(lat lon) model(invalid)")

  # Invalid knn type/value
  with pytest.raises(ParseError, match="spregress option knn must be at least 1"):
    parse_command("spregress y x, coord(lat lon) knn(-1)")

  # Unsupported option
  with pytest.raises(ParseError, match="spregress unsupported option: invalid_opt"):
    parse_command("spregress y x, coord(lat lon) invalid_opt")


def test_execute_spregress_lag(tmp_path: Path) -> None:
  path = tmp_path / "spatial_lag.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=False,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, SpatialRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.model_type == "lag"
  assert result.coord_variables == ("lat", "lon")
  assert result.knn == 3
  assert result.observation_count == 8
  assert len(result.coefficients) == 3  # intercept, x, rho
  assert result.coefficients[0].name == "intercept"
  assert result.coefficients[1].name == "x"
  assert result.coefficients[2].name == "rho"
  assert result.spatial_coefficient_name == "rho"
  assert isinstance(result.spatial_coefficient, float)
  assert isinstance(result.r_squared, float)


def test_execute_spregress_error(tmp_path: Path) -> None:
  path = tmp_path / "spatial_err.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="error",
        coord_variables=("lat", "lon"),
        knn=4,
        robust=False,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, SpatialRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.model_type == "error"
  assert result.coord_variables == ("lat", "lon")
  assert result.knn == 4
  assert result.observation_count == 8
  assert len(result.coefficients) == 3  # intercept, x, lambda
  assert result.coefficients[0].name == "intercept"
  assert result.coefficients[1].name == "x"
  assert result.coefficients[2].name == "lambda"
  assert result.spatial_coefficient_name == "lambda"


def test_execute_spregress_robust(tmp_path: Path) -> None:
  path = tmp_path / "spatial_robust.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    # robust lag
    result_lag = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=True,
      )
    )
    # robust error
    result_err = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="error",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=True,
      )
    )
  finally:
    executor.close()

  assert isinstance(result_lag, SpatialRegressionResult)
  assert result_lag.robust is True
  assert result_lag.spatial_coefficient_name == "rho"

  assert isinstance(result_err, SpatialRegressionResult)
  assert result_err.robust is True
  assert result_err.spatial_coefficient_name == "lambda"


def test_execute_spregress_predict(tmp_path: Path) -> None:
  path = tmp_path / "spatial_predict.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=False,
      )
    )
    # Exogenous prediction (xb)
    predict_res = executor.execute(
      PredictCommand(
        target_variable="y_hat",
        kind="xb",
      )
    )
    spatial_predict_res = executor.execute(
      PredictCommand(
        target_variable="y_full",
        kind="spatial_lag",
      )
    )

    # Predict non-xb must fail
    with pytest.raises(
      ExecutionError,
      match="predict only supports xb and spatial_lag after spregress",
    ):
      executor.execute(PredictCommand(target_variable="y_res", kind="residuals"))
  finally:
    executor.close()

  assert predict_res is not None
  assert spatial_predict_res is not None
  # Active dataset in state should now contain y_hat column
  active_ds = executor.state.active_dataset
  assert active_ds is not None
  assert "y_hat" in [col.name for col in active_ds.columns]
  assert "y_full" in [col.name for col in active_ds.columns]


def test_execute_spregress_error_rejects_spatial_lag_predict(tmp_path: Path) -> None:
  path = tmp_path / "spatial_error_predict.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="error",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=False,
      )
    )
    with pytest.raises(
      ExecutionError,
      match="predict spatial_lag is only available after spregress model\\(lag\\)",
    ):
      executor.execute(PredictCommand(target_variable="y_full", kind="spatial_lag"))
  finally:
    executor.close()


def test_spregress_shell_autocomplete() -> None:
  assert "spregress" in COMMAND_NAMES
  completions = list(_option_completions("spregress", ""))
  completion_texts = [c.text for c in completions]
  assert "coord(" in completion_texts
  assert "model(" in completion_texts
  assert "knn(" in completion_texts
  assert "robust" in completion_texts


def test_spregress_help_topic() -> None:
  topics = available_help_topics()
  assert "spregress" in topics

  text = load_help_topic("spregress")
  assert "spregress" in text
  assert "coord(" in text
  assert "Examples:" in text

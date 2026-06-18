from pathlib import Path

import duckdb
import pytest

from tabdat.errors import ExecutionError, ParseError
from tabdat.executor import Executor
from tabdat.help import available_help_topics, load_help_topic
from tabdat.models import (
  BinaryExpression,
  EstatCommand,
  IdentifierExpression,
  NumberExpression,
  PredictCommand,
  RegressCommand,
  RidgeCommand,
  SpatialRegressionResult,
  SpregressCommand,
  StringExpression,
  TableResult,
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

  # Custom model(sarar), knn, robust
  assert parse_command(
    "spregress y x, coord(lat lon) model(sarar) knn(3) robust"
  ) == SpregressCommand(
    outcome="y",
    predictors=("x",),
    model_type="sarar",
    coord_variables=("lat", "lon"),
    knn=3,
    robust=True,
  )


def test_parse_spregress_errors() -> None:
  # Missing coord / weights option
  with pytest.raises(
    ParseError, match="spregress requires either coord\\(\\) or weights\\(\\) option"
  ):
    parse_command("spregress y x")

  # coord with 1 variable
  with pytest.raises(ParseError, match="spregress option coord expects exactly two variables"):
    parse_command("spregress y x, coord(lat)")

  # coord with 3 variables
  with pytest.raises(ParseError, match="spregress option coord expects exactly two variables"):
    parse_command("spregress y x, coord(lat lon alt)")

  # Invalid model type
  with pytest.raises(ParseError, match="spregress option model must be 'lag', 'error', or 'sarar'"):
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


def test_execute_spregress_sarar(tmp_path: Path) -> None:
  path = tmp_path / "spatial_sarar.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="sarar",
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
  assert result.model_type == "sarar"
  assert result.coord_variables == ("lat", "lon")
  assert result.knn == 3
  assert result.observation_count == 8
  assert len(result.coefficients) == 4  # intercept, x, rho, lambda
  assert result.coefficients[0].name == "intercept"
  assert result.coefficients[1].name == "x"
  assert result.coefficients[2].name == "rho"
  assert result.coefficients[3].name == "lambda"
  assert result.spatial_coefficient_name == "rho"
  assert isinstance(result.spatial_coefficient, float)
  assert result.coefficients[3].standard_error is None  # GMM non-robust combo omits lambda std err


def test_execute_spregress_sarar_robust(tmp_path: Path) -> None:
  path = tmp_path / "spatial_sarar_robust.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="sarar",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=True,
      )
    )
  finally:
    executor.close()

  assert isinstance(result, SpatialRegressionResult)
  assert result.outcome == "y"
  assert result.predictors == ("x",)
  assert result.model_type == "sarar"
  assert result.coord_variables == ("lat", "lon")
  assert result.knn == 3
  assert result.observation_count == 8
  assert len(result.coefficients) == 4  # intercept, x, rho, lambda
  assert result.coefficients[0].name == "intercept"
  assert result.coefficients[1].name == "x"
  assert result.coefficients[2].name == "rho"
  assert result.coefficients[3].name == "lambda"
  assert result.spatial_coefficient_name == "rho"
  assert isinstance(result.spatial_coefficient, float)
  assert isinstance(
    result.coefficients[3].standard_error, float
  )  # GM_Combo_Het computes lambda std err


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


def test_execute_spregress_predict_supports_mismatched_sample(tmp_path: Path) -> None:
  path = tmp_path / "spatial_mismatch.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    load_result = executor.execute(UseCommand(path))
    assert load_result is not None
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
    dataset = executor.state.active_dataset
    assert dataset is not None
    next_dataset = executor.backend.filter_rows(
      dataset,
      BinaryExpression(
        left=IdentifierExpression("x"),
        operator=">",
        right=NumberExpression(1.0),
      ),
      keep=True,
    )
    executor.state.active_dataset = next_dataset
    predict_res = executor.execute(PredictCommand(target_variable="y_full", kind="spatial_lag"))
    assert predict_res is not None
    assert "y_full" in [col.name for col in executor.state.active_dataset.columns]
  finally:
    executor.close()


def test_execute_spregress_predict_ignores_stale_ridge_state(tmp_path: Path) -> None:
  path = tmp_path / "spatial_state_isolation.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(RidgeCommand(outcome="y", predictors=("x",), alpha=1.0))
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
    predict_res = executor.execute(
      PredictCommand(
        target_variable="y_full",
        kind="spatial_lag",
      )
    )
  finally:
    executor.close()

  assert predict_res is not None


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


def test_parse_spregress_weights_options() -> None:
  # Default contiguity(queen)
  assert parse_command("spregress y x1 x2, weights(path/to/w.gal) id(station)") == SpregressCommand(
    outcome="y",
    predictors=("x1", "x2"),
    model_type="lag",
    coord_variables=None,
    knn=None,
    weights_file="path/to/w.gal",
    id_variable="station",
    contiguity="queen",
    robust=False,
  )

  # Custom contiguity, model, robust
  assert parse_command(
    "spregress y x, weights(w.shp) id(station) contiguity(rook) model(error) robust"
  ) == SpregressCommand(
    outcome="y",
    predictors=("x",),
    model_type="error",
    coord_variables=None,
    knn=None,
    weights_file="w.shp",
    id_variable="station",
    contiguity="rook",
    robust=True,
  )


def test_parse_spregress_weights_errors() -> None:
  # Conflict: both coord and weights
  with pytest.raises(
    ParseError,
    match="spregress option coord and weights are mutually exclusive",
  ):
    parse_command("spregress y x, coord(lat lon) weights(w.gal) id(station)")

  # Missing ID when weights is specified
  with pytest.raises(
    ParseError,
    match="spregress option id\\(\\) is required when weights\\(\\) is specified",
  ):
    parse_command("spregress y x, weights(w.gal)")

  # Missing weights/coord
  with pytest.raises(
    ParseError,
    match="spregress requires either coord\\(\\) or weights\\(\\) option",
  ):
    parse_command("spregress y x, id(station)")

  # Invalid contiguity
  with pytest.raises(ParseError, match="spregress option contiguity must be 'queen' or 'rook'"):
    parse_command("spregress y x, weights(w.shp) id(station) contiguity(invalid)")

  # Unrecognized option with weights (e.g. knn)
  with pytest.raises(
    ParseError,
    match="spregress option knn/coord can only be used with coord\\(\\)",
  ):
    parse_command("spregress y x, weights(w.shp) id(station) knn(3)")

  # Contiguity with coord option
  with pytest.raises(
    ParseError,
    match="spregress option contiguity can only be used with weights\\(\\)",
  ):
    parse_command("spregress y x, coord(lat lon) contiguity(queen)")


def test_execute_spregress_weights_gal_gwt(tmp_path: Path) -> None:
  import duckdb
  import pandas as pd

  data_path = tmp_path / "data.parquet"
  df = pd.DataFrame(
    {"y": [10.0, 12.0, 15.0, 18.0], "x": [1.0, 2.0, 3.0, 4.0], "id": ["A", "B", "C", "D"]}
  )
  assert len(df) == 4
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  # Write .gal file
  # Format:
  # 0 4
  # A 2
  # B C
  # B 2
  # A D
  # C 2
  # A D
  # D 2
  # B C
  gal_path = tmp_path / "w.gal"
  gal_path.write_text("0 4 test GAL\nA 2\nB C\nB 2\nA D\nC 2\nA D\nD 2\nB C\n")

  # Write .gwt file
  gwt_path = tmp_path / "w.gwt"
  gwt_path.write_text(
    "0 4 test.shp STATION\nA B 1.0\nA C 1.0\nB A 1.0\nB D 1.0\nC A 1.0\nC D 1.0\nD B 1.0\nD C 1.0\n"
  )

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))

    # GAL execution
    result_gal = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        weights_file=str(gal_path),
        id_variable="id",
        contiguity="queen",
        robust=False,
      )
    )
    assert isinstance(result_gal, SpatialRegressionResult)
    assert result_gal.observation_count == 4
    assert len(result_gal.coefficients) == 3

    # GWT execution
    result_gwt = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        weights_file=str(gwt_path),
        id_variable="id",
        contiguity="queen",
        robust=False,
      )
    )
    assert isinstance(result_gwt, SpatialRegressionResult)
    assert result_gwt.observation_count == 4
  finally:
    executor.close()


def test_execute_spregress_weights_shp(tmp_path: Path) -> None:
  import libpysal

  shp_path = libpysal.examples.get_path("baltim.shp")
  dbf_path = libpysal.examples.get_path("baltim.dbf")

  db = libpysal.io.open(dbf_path)
  df = db.to_df()
  # Normalize columns
  df.columns = [c.lower() for c in df.columns]

  import duckdb

  data_path = tmp_path / "baltim.parquet"
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    result = executor.execute(
      SpregressCommand(
        outcome="price",
        predictors=("nroom", "age"),
        model_type="lag",
        weights_file=shp_path,
        id_variable="station",
        contiguity="queen",
        robust=False,
      )
    )
    assert isinstance(result, SpatialRegressionResult)
    assert result.observation_count == len(df)

    # Predict xb
    predict_xb = executor.execute(
      PredictCommand(
        target_variable="price_hat",
        kind="xb",
      )
    )
    assert predict_xb is not None

    # Predict spatial_lag
    predict_lag = executor.execute(
      PredictCommand(
        target_variable="price_lag",
        kind="spatial_lag",
      )
    )
    assert predict_lag is not None

    active_ds = executor.state.active_dataset
    assert active_ds is not None
    columns = [col.name for col in active_ds.columns]
    assert "price_hat" in columns
    assert "price_lag" in columns
  finally:
    executor.close()


def test_execute_spregress_weights_errors(tmp_path: Path) -> None:
  import duckdb
  import pandas as pd

  data_path = tmp_path / "data_err.parquet"
  df = pd.DataFrame({"y": [10.0, 12.0, 15.0], "x": [1.0, 2.0, 3.0], "id": ["A", "B", "C"]})
  assert len(df) == 3
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  gal_path = tmp_path / "w_err.gal"
  gal_path.write_text("0 3 test GAL\nA 1\nB\nB 1\nA\nC 0\n")

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))

    # 1. Non-existent file
    with pytest.raises(ExecutionError, match="weights file not found"):
      executor.execute(
        SpregressCommand(
          outcome="y",
          predictors=("x",),
          model_type="lag",
          weights_file="nonexistent.gal",
          id_variable="id",
          contiguity="queen",
          robust=False,
        )
      )

    # 2. Unsupported extension
    txt_path = tmp_path / "w.txt"
    txt_path.write_text("dummy")
    with pytest.raises(ExecutionError, match="unsupported weights file format"):
      executor.execute(
        SpregressCommand(
          outcome="y",
          predictors=("x",),
          model_type="lag",
          weights_file=str(txt_path),
          id_variable="id",
          contiguity="queen",
          robust=False,
        )
      )

    # 3. ID column not in active dataset
    with pytest.raises(ExecutionError, match="id variable 'missing_id' not found"):
      executor.execute(
        SpregressCommand(
          outcome="y",
          predictors=("x",),
          model_type="lag",
          weights_file=str(gal_path),
          id_variable="missing_id",
          contiguity="queen",
          robust=False,
        )
      )

    # 4. ID mismatch (missing IDs in weights file)
    # Create a dataset with ID D, which is not in the gal file (A, B, C)
    df_mismatch = pd.DataFrame(
      {"y": [10.0, 12.0, 15.0], "x": [1.0, 2.0, 3.0], "id": ["A", "B", "D"]}
    )
    assert len(df_mismatch) == 3
    mismatch_data_path = tmp_path / "mismatch.parquet"
    con.execute("copy df_mismatch to ? (format parquet)", [str(mismatch_data_path)])
    executor.execute(UseCommand(mismatch_data_path))

    with pytest.raises(
      ExecutionError,
      match="some regression sample IDs are missing from the spatial weights",
    ):
      executor.execute(
        SpregressCommand(
          outcome="y",
          predictors=("x",),
          model_type="lag",
          weights_file=str(gal_path),
          id_variable="id",
          contiguity="queen",
          robust=False,
        )
      )
  finally:
    executor.close()


def test_execute_spregress_weights_edge_cases(tmp_path: Path) -> None:
  import shutil

  import duckdb
  import libpysal
  import pandas as pd

  # Write a base parquet data path
  data_path = tmp_path / "data_edge.parquet"
  df = pd.DataFrame({"y": [10.0, 12.0, 15.0], "x": [1.0, 2.0, 3.0], "id": ["A", "B", "C"]})
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])
  _ = df

  gal_path = tmp_path / "w_edge.gal"
  gal_path.write_text("0 3 test GAL\nA 1\nB\nB 1\nA\nC 0\n")

  executor = Executor()
  try:
    # 1. Duplicate IDs check
    df_dup = pd.DataFrame({"y": [10.0, 12.0, 15.0], "x": [1.0, 2.0, 3.0], "id": ["A", "A", "C"]})
    dup_data_path = tmp_path / "dup.parquet"
    con.execute("copy df_dup to ? (format parquet)", [str(dup_data_path)])
    _ = df_dup
    executor.execute(UseCommand(dup_data_path))

    with pytest.raises(ExecutionError, match="contains duplicate values"):
      executor.execute(
        SpregressCommand(
          outcome="y",
          predictors=("x",),
          model_type="lag",
          weights_file=str(gal_path),
          id_variable="id",
          contiguity="queen",
          robust=False,
        )
      )

    # 2. Float IDs to string conversion check (1.0 -> "1" matching string keys "1", "2", "3")
    df_float_id = pd.DataFrame(
      {"y": [10.0, 12.0, 15.0], "x": [1.0, 2.0, 3.0], "id": [1.0, 2.0, 3.0]}
    )
    float_id_data_path = tmp_path / "float_id.parquet"
    con.execute("copy df_float_id to ? (format parquet)", [str(float_id_data_path)])
    _ = df_float_id
    executor.execute(UseCommand(float_id_data_path))

    gal_num_path = tmp_path / "w_num.gal"
    gal_num_path.write_text("0 3 test GAL\n1 1\n2\n2 1\n1\n3 0\n")

    result_float = executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        weights_file=str(gal_num_path),
        id_variable="id",
        contiguity="queen",
        robust=False,
      )
    )
    assert isinstance(result_float, SpatialRegressionResult)

    # 3. Uppercase DBF check
    shp_src = libpysal.examples.get_path("baltim.shp")
    dbf_src = libpysal.examples.get_path("baltim.dbf")
    shx_src = libpysal.examples.get_path("baltim.shx")

    shp_dest = tmp_path / "BALTIM.SHP"
    dbf_dest = tmp_path / "BALTIM.DBF"
    shx_dest = tmp_path / "BALTIM.SHX"
    shutil.copy(shp_src, shp_dest)
    shutil.copy(dbf_src, dbf_dest)
    shutil.copy(shx_src, shx_dest)

    db = libpysal.io.open(str(dbf_dest))
    df_balt = db.to_df()
    df_balt.columns = [c.lower() for c in df_balt.columns]
    balt_data_path = tmp_path / "baltim_edge.parquet"
    con.execute("copy df_balt to ? (format parquet)", [str(balt_data_path)])
    db.close()

    executor.execute(UseCommand(balt_data_path))
    result_shp = executor.execute(
      SpregressCommand(
        outcome="price",
        predictors=("nroom", "age"),
        model_type="lag",
        weights_file=str(shp_dest),
        id_variable="station",
        contiguity="queen",
        robust=False,
      )
    )
    assert isinstance(result_shp, SpatialRegressionResult)

  finally:
    executor.close()


def test_spregress_shell_autocomplete_updated() -> None:
  completions = list(_option_completions("spregress", ""))
  completion_texts = [c.text for c in completions]
  assert "weights(" in completion_texts
  assert "id(" in completion_texts
  assert "contiguity(" in completion_texts


def test_execute_estat_spatial_preconditions(tmp_path: Path) -> None:
  import duckdb
  import pandas as pd

  data_path = tmp_path / "data.parquet"
  df = pd.DataFrame({"y": [1.0, 2.0], "x": [3.0, 4.0], "lat": [0.0, 1.0], "lon": [1.0, 0.0]})  # noqa: F841
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    # No prior regress model
    with pytest.raises(ExecutionError, match="estat spatial requires a prior regress model"):
      executor.execute(EstatCommand(subcommand="spatial", coord_variables=("lat", "lon"), knn=1))
  finally:
    executor.close()


def test_execute_estat_spatial_knn(tmp_path: Path) -> None:
  import duckdb
  import pandas as pd

  data_path = tmp_path / "data.parquet"
  df = pd.DataFrame(  # noqa: F841
    {
      "y": [1.0, 2.0, 3.0, 4.0, 5.0],
      "x": [2.0, 3.0, 4.0, 5.0, 6.0],
      "lat": [0.0, 0.0, 1.0, 1.0, 0.5],
      "lon": [0.0, 1.0, 0.0, 1.0, 0.5],
    }
  )
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))

    result = executor.execute(
      EstatCommand(subcommand="spatial", coord_variables=("lat", "lon"), knn=2)
    )
    assert isinstance(result, TableResult)
    assert result.headers == ("Test", "Statistic", "df / z-value", "p-value")
    assert len(result.rows) == 6

    # Moran's I
    assert result.rows[0][0] == "Moran's I (residual)"
    # LM error
    assert result.rows[1][0] == "LM error"
    assert result.rows[1][2] == 1
    # LM lag
    assert result.rows[2][0] == "LM lag"
    assert result.rows[2][2] == 1
    # Robust LM error
    assert result.rows[3][0] == "Robust LM error"
    assert result.rows[3][2] == 1
    # Robust LM lag
    assert result.rows[4][0] == "Robust LM lag"
    assert result.rows[4][2] == 1
    # LM SARMA
    assert result.rows[5][0] == "LM SARMA"
    assert result.rows[5][2] == 2

    # Check that values are finite float or None
    for row in result.rows:
      assert row[1] is None or isinstance(row[1], float)
      assert row[2] is None or isinstance(row[2], (int, float))
      assert row[3] is None or isinstance(row[3], float)
  finally:
    executor.close()


def test_execute_estat_spatial_weights_file(tmp_path: Path) -> None:
  import duckdb
  import pandas as pd

  data_path = tmp_path / "data.parquet"
  df = pd.DataFrame(  # noqa: F841
    {"y": [10.0, 12.0, 15.0, 18.0], "x": [1.0, 2.0, 3.0, 4.0], "id": ["A", "B", "C", "D"]}
  )
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  gal_path = tmp_path / "w.gal"
  gal_path.write_text("0 4 test GAL\nA 2\nB C\nB 2\nA D\nC 2\nA D\nD 2\nB C\n")

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))

    result = executor.execute(
      EstatCommand(
        subcommand="spatial",
        weights_file=str(gal_path),
        id_variable="id",
        contiguity="queen",
      )
    )
    assert isinstance(result, TableResult)
    assert result.headers == ("Test", "Statistic", "df / z-value", "p-value")
    assert len(result.rows) == 6
  finally:
    executor.close()


def test_execute_estat_spatial_sample_alignment_error(tmp_path: Path) -> None:
  import duckdb
  import pandas as pd

  data_path = tmp_path / "data.parquet"
  # One missing coordinate row
  df = pd.DataFrame(  # noqa: F841
    {
      "y": [1.0, 2.0, 3.0, 4.0, 5.0],
      "x": [2.0, 3.0, 4.0, 5.0, 6.0],
      "lat": [0.0, 0.0, 1.0, 1.0, None],
      "lon": [0.0, 1.0, 0.0, 1.0, 0.5],
    }
  )
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))

    # Since the last row has a missing lat coordinate, estat spatial will only
    # find 4 complete cases, but regress estimated on 5 cases. This sample size
    # mismatch should trigger an error.
    with pytest.raises(
      ExecutionError,
      match="estat spatial sample size \\(4\\) does not match OLS estimation sample size \\(5\\)",
    ):
      executor.execute(EstatCommand(subcommand="spatial", coord_variables=("lat", "lon"), knn=2))
  finally:
    executor.close()


def test_estat_spatial_shell_autocomplete() -> None:

  from tabdat.shell import _ESTAT_SPATIAL_OPTIONS, _ESTAT_SUBCOMMANDS

  # Check that "spatial" is in the subcommands list
  assert "spatial" in _ESTAT_SUBCOMMANDS

  # Check options completion list
  assert "coord(" in _ESTAT_SPATIAL_OPTIONS
  assert "knn(" in _ESTAT_SPATIAL_OPTIONS
  assert "weights(" in _ESTAT_SPATIAL_OPTIONS
  assert "id(" in _ESTAT_SPATIAL_OPTIONS
  assert "contiguity(" in _ESTAT_SPATIAL_OPTIONS


def test_execute_spregress_predict_mismatched_variables(tmp_path: Path) -> None:
  path = tmp_path / "spatial_mismatched_vars.parquet"
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
    mismatched_path = tmp_path / "mismatched.parquet"
    _write_sql_parquet(
      mismatched_path,
      """
      select * from (
        values
          (10.0, 1.0),
          (12.0, 2.0)
      ) as d(y, x)
      """,
    )
    executor.execute(UseCommand(mismatched_path))
    with pytest.raises(
      ExecutionError,
      match="predict requires a prior spregress model with matching variables",
    ):
      executor.execute(PredictCommand(target_variable="y_full", kind="spatial_lag"))
  finally:
    executor.close()


def test_execute_spregress_predict_sarar_out_of_sample(tmp_path: Path) -> None:
  path = tmp_path / "spatial_sarar_oos.parquet"
  _write_spatial_parquet(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="sarar",
        coord_variables=("lat", "lon"),
        knn=3,
        robust=True,
      )
    )
    dataset = executor.state.active_dataset
    assert dataset is not None
    next_dataset = executor.backend.filter_rows(
      dataset,
      BinaryExpression(
        left=IdentifierExpression("x"),
        operator="<=",
        right=NumberExpression(6.0),
      ),
      keep=True,
    )
    executor.state.active_dataset = next_dataset
    predict_res = executor.execute(PredictCommand(target_variable="y_full", kind="spatial_lag"))
    assert predict_res is not None
    active_ds = executor.state.active_dataset
    assert "y_full" in [col.name for col in active_ds.columns]
  finally:
    executor.close()


def test_execute_spregress_predict_weights_file_out_of_sample(tmp_path: Path) -> None:
  import pandas as pd

  data_path = tmp_path / "data_oos.parquet"
  df = pd.DataFrame(
    {"y": [10.0, 12.0, 15.0, 18.0], "x": [1.0, 2.0, 3.0, 4.0], "id": ["A", "B", "C", "D"]}
  )
  assert len(df) == 4
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  gal_path = tmp_path / "w_oos.gal"
  gal_path.write_text("0 4 test GAL\nA 2\nB C\nB 2\nA D\nC 2\nA D\nD 2\nB C\n")

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        weights_file=str(gal_path),
        id_variable="id",
      )
    )

    # Filter rows to B, C, D (out-of-sample subset)
    dataset = executor.state.active_dataset
    assert dataset is not None
    next_dataset = executor.backend.filter_rows(
      dataset,
      BinaryExpression(
        left=IdentifierExpression("id"),
        operator="!=",
        right=StringExpression("A"),
      ),
      keep=True,
    )
    executor.state.active_dataset = next_dataset
    predict_res = executor.execute(PredictCommand(target_variable="y_full", kind="spatial_lag"))
    assert predict_res is not None
    assert "y_full" in [col.name for col in executor.state.active_dataset.columns]
  finally:
    executor.close()


def test_execute_spregress_predict_duplicate_ids_fails(tmp_path: Path) -> None:
  import pandas as pd

  data_path = tmp_path / "data_dup.parquet"
  df = pd.DataFrame(
    {"y": [10.0, 12.0, 15.0, 18.0], "x": [1.0, 2.0, 3.0, 4.0], "id": ["A", "B", "C", "D"]}
  )
  assert len(df) == 4
  con = duckdb.connect()
  con.execute("copy df to ? (format parquet)", [str(data_path)])

  gal_path = tmp_path / "w_dup.gal"
  gal_path.write_text("0 4 test GAL\nA 2\nB C\nB 2\nA D\nC 2\nA D\nD 2\nB C\n")

  executor = Executor()
  try:
    executor.execute(UseCommand(data_path))
    executor.execute(
      SpregressCommand(
        outcome="y",
        predictors=("x",),
        model_type="lag",
        weights_file=str(gal_path),
        id_variable="id",
      )
    )

    dup_df = pd.DataFrame(
      {"y": [12.0, 12.0, 15.0, 18.0], "x": [2.0, 2.0, 3.0, 4.0], "id": ["B", "B", "C", "D"]}
    )
    assert len(dup_df) == 4
    dup_path = tmp_path / "data_dup_target.parquet"
    con.execute("copy dup_df to ? (format parquet)", [str(dup_path)])

    executor.execute(UseCommand(dup_path))
    with pytest.raises(
      ExecutionError,
      match="id variable 'id' contains duplicate values in the prediction sample",
    ):
      executor.execute(PredictCommand(target_variable="y_full", kind="spatial_lag"))
  finally:
    executor.close()

from pathlib import Path

import pytest

from tabdat.cli import main
from tabdat.errors import ExecutionError
from tabdat.executor import Executor
from tabdat.models import (
  RegressCommand,
  UseCommand,
)
from tabdat.parser import parse_command


def _write_sample_data(path: Path) -> None:
  import polars as pl

  # Write a Parquet file with some missing values to test e(sample) mask
  df = pl.DataFrame(
    {
      "y": [1.0, 2.0, None, 4.0, 5.0],
      "x": [10.0, None, 30.0, 40.0, 50.0],
      "z": [100.0, 200.0, 300.0, 400.0, 500.0],
    }
  )
  df.write_parquet(path)


def test_esample_compilation_and_hiding(tmp_path: Path) -> None:
  data_path = tmp_path / "sample.parquet"
  _write_sample_data(data_path)

  executor = Executor()
  try:
    # 1. Before running estimation, e(sample) should fail
    executor.execute(UseCommand(data_path))

    # Asserting __esample is not in active columns info
    dataset_info = executor.state.active_dataset
    assert not any(c.name == "__esample" for c in dataset_info.columns)

    with pytest.raises(ExecutionError, match="no active estimation sample available"):
      executor.execute(parse_command("generate in_sample = e(sample)"))

    # 2. Fit a model (observations 2 and 3 have missing values, so rows 0, 3, 4 are valid)
    executor.execute(RegressCommand(outcome="y", predictors=("x",)))

    # Asserting __esample is hidden from public dataset columns
    dataset_info = executor.state.active_dataset
    assert not any(c.name == "__esample" for c in dataset_info.columns)

    # 3. Generate a column using e(sample)
    executor.execute(parse_command("generate in_sample = e(sample)"))

    # 4. Fetch the values to check correctness
    rows = executor.backend.regression_rows(executor.state.active_dataset, ("in_sample",))
    values = [r[0] for r in rows]
    assert values == [True, False, False, True, True]

    # 5. Invalid arguments to e() should raise correct error
    with pytest.raises(ExecutionError, match="e\\(\\) requires exactly one argument 'sample'"):
      executor.execute(parse_command("generate bad = e(age)"))

  finally:
    executor.close()


def test_cli_exit_codes(tmp_path: Path) -> None:
  data_path = tmp_path / "sample.parquet"
  _write_sample_data(data_path)

  # Exit code 0 on success
  assert main(["-c", f"use {data_path}", "-c", "regress y x"]) == 0

  # Exit code 2 on parse / syntax error
  assert main(["-c", "generate x ="]) == 2

  # Exit code 1 on execution error (e.g. missing column)
  assert main(["-c", f"use {data_path}", "-c", "regress y missing_col"]) == 1

  # Exit code 3 on missing script file
  assert main(["-f", "this_file_does_not_exist.td"]) == 3

  # Exit code 3 on missing config file
  assert main(["--config", "missing_config.toml", "-c", "count"]) == 3

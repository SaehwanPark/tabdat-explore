from pathlib import Path

import duckdb
import pandas as pd
import pytest


@pytest.fixture
def sample_parquet(tmp_path: Path) -> Path:
  path = tmp_path / "patients.parquet"
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      """
      copy (
        select * from (
          values
            (30, 22.5, 'F', 100.0),
            (42, 25.0, 'M', 150.0),
            (54, 27.5, 'F', null)
        ) as patients(age, bmi, sex, cost)
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()
  return path


@pytest.fixture
def sample_dta(tmp_path: Path) -> Path:
  path = tmp_path / "patients.dta"
  frame = pd.DataFrame(
    {
      "age": [30, 42, 54],
      "bmi": [22.5, 25.0, 27.5],
      "sex": ["F", "M", "F"],
      "cost": [100.0, 150.0, None],
    }
  )
  frame.to_stata(path, write_index=False)
  return path

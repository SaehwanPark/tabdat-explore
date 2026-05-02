from pathlib import Path

import duckdb
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

"""DuckDB-backed dataset operations."""

from pathlib import Path

import duckdb

from tabdat.errors import ExecutionError
from tabdat.models import ColumnInfo, DatasetInfo, SummaryRow

NUMERIC_TYPES = (
  "TINYINT",
  "SMALLINT",
  "INTEGER",
  "BIGINT",
  "HUGEINT",
  "UTINYINT",
  "USMALLINT",
  "UINTEGER",
  "UBIGINT",
  "FLOAT",
  "DOUBLE",
  "DECIMAL",
)


class DuckDBBackend:
  """Small DuckDB adapter for the Phase 1 active Parquet dataset."""

  def __init__(self) -> None:
    self._connection = duckdb.connect(database=":memory:")

  def close(self) -> None:
    self._connection.close()

  def inspect_parquet(self, path: Path) -> DatasetInfo:
    normalized = path.expanduser()
    if normalized.suffix.lower() != ".parquet":
      raise ExecutionError("use only supports local .parquet files in Phase 1")
    if not normalized.exists():
      raise ExecutionError(f"use could not find file: {path}")
    if not normalized.is_file():
      raise ExecutionError(f"use expected a file path: {path}")

    path_arg = str(normalized)
    try:
      description = self._connection.execute(
        "describe select * from read_parquet(?)",
        [path_arg],
      ).fetchall()
      row_count = self._connection.execute(
        "select count(*) from read_parquet(?)",
        [path_arg],
      ).fetchone()[0]
    except duckdb.Error as exc:
      raise ExecutionError(f"use could not read Parquet file: {path}") from exc

    columns = tuple(ColumnInfo(name=row[0], data_type=row[1]) for row in description)
    return DatasetInfo(path=normalized, row_count=row_count, columns=columns)

  def summarize(self, dataset: DatasetInfo, variables: tuple[str, ...]) -> tuple[SummaryRow, ...]:
    column_types = {column.name: column.data_type.upper() for column in dataset.columns}
    requested = variables or tuple(
      column.name for column in dataset.columns if _is_numeric_type(column.data_type)
    )

    if not requested:
      raise ExecutionError("summarize found no numeric columns")

    missing = tuple(variable for variable in requested if variable not in column_types)
    if missing:
      raise ExecutionError(f"summarize unknown variable: {', '.join(missing)}")

    non_numeric = tuple(
      variable for variable in requested if not _is_numeric_type(column_types[variable])
    )
    if non_numeric:
      raise ExecutionError(f"summarize requires numeric variables: {', '.join(non_numeric)}")

    rows = tuple(self._summarize_variable(dataset.path, variable) for variable in requested)
    return rows

  def _summarize_variable(self, path: Path, variable: str) -> SummaryRow:
    quoted_variable = _quote_identifier(variable)
    sql = f"""
      select
        count({quoted_variable}) as count,
        avg({quoted_variable}) as mean,
        stddev_samp({quoted_variable}) as std_dev,
        min({quoted_variable}) as minimum,
        max({quoted_variable}) as maximum
      from read_parquet(?)
    """
    try:
      count, mean, std_dev, minimum, maximum = self._connection.execute(
        sql,
        [str(path)],
      ).fetchone()
    except duckdb.Error as exc:
      raise ExecutionError(f"summarize failed for variable: {variable}") from exc

    return SummaryRow(
      variable=variable,
      count=count,
      mean=mean,
      std_dev=std_dev,
      minimum=minimum,
      maximum=maximum,
    )


def _is_numeric_type(data_type: str) -> bool:
  normalized = data_type.upper()
  return normalized.startswith(NUMERIC_TYPES)


def _quote_identifier(identifier: str) -> str:
  escaped = identifier.replace('"', '""')
  return f'"{escaped}"'

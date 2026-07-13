"""DuckDB-backed dataset operations."""

import math
import tempfile
from collections.abc import Callable, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Literal, cast
from urllib.error import URLError
from urllib.parse import urlparse

import duckdb
import pandas as pd
import polars as pl
from polars.exceptions import PolarsError
from pydantic.dataclasses import dataclass

from tabdat.errors import (
  BackendExecutionError,
  ExecutionError,
  ReservedNameError,
  TypeMismatchExecutionError,
  UnknownVariableError,
)
from tabdat.extension_registry import (
  DataFormat,
  ingestion_adapter_for,
  lazy_engine_supported,
  lazy_mode_supported,
  remote_scheme_supported,
)
from tabdat.models import (
  BinaryExpression,
  CodebookRow,
  ColumnInfo,
  DatasetInfo,
  Expression,
  FunctionCallExpression,
  IdentifierExpression,
  NullExpression,
  NumberExpression,
  PanelMetadata,
  PanelStructureSummary,
  RecodeRange,
  RecodeRule,
  StringExpression,
  SummaryRow,
  UnaryExpression,
)

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
  "INT8",
  "INT16",
  "INT32",
  "INT64",
  "UINT8",
  "UINT16",
  "UINT32",
  "UINT64",
  "FLOAT32",
  "FLOAT64",
  "FLOAT",
  "DOUBLE",
  "DECIMAL",
)
UNSIGNED_NUMERIC_TYPES = (
  "UTINYINT",
  "USMALLINT",
  "UINTEGER",
  "UBIGINT",
  "UINT8",
  "UINT16",
  "UINT32",
  "UINT64",
)
ExpressionDomain = Literal["numeric", "string", "boolean", "other", "null"]
TabulateCellKey = tuple[tuple[tuple[str, object], ...], tuple[tuple[str, object], ...]]
SUPPORTED_FUNCTIONS = {"abs", "ceil", "floor", "ln", "log", "lower", "round", "sqrt", "upper"}
NUMERIC_FUNCTIONS = {"abs", "ceil", "floor", "ln", "log", "round", "sqrt"}
NULL_LITERAL_ERROR = "null literal only supports equality and inequality comparisons"
UNSIGNED_ARITHMETIC_ERROR = (
  "expression type mismatch: unsigned numeric values do not support subtraction or unary minus"
)
ACTIVE_TABLE = "__tabdat_active"
ACTIVE_VIEW = "active"
NEXT_ACTIVE_TABLE = "__tabdat_next"
NEXT_ACTIVE_VIEW = "__tabdat_next_view"


@dataclass(frozen=True)
class LoadSource:
  format: Literal["parquet", "stata", "csv", "feather", "arrow"]
  read_path: str
  display_path: Path | str
  is_remote: bool


class DuckDBBackend:
  """The storage and execution adapter wrapping an in-memory DuckDB connection.

  Responsible for ingesting local/remote files (Parquet, CSV, Stata, Arrow, Feather),
  managing eager/lazy query execution (via Polars or DuckDB), compiling schema definitions,
  executing SQL scripts, and preparing query frames for analysis or plotting.
  """

  def __init__(self) -> None:
    """Initialize the backend connection and internal state variables."""
    self._connection = duckdb.connect(database=":memory:")
    # Head/tail, filters, and row-preserving rewrites expose the active sequence. Keep DuckDB's
    # insertion-order behavior explicit instead of relying on its connection default.
    self._connection.execute("set preserve_insertion_order = true")
    self._active_storage: Literal["table", "view"] = "table"
    self._lazy_engine: Literal["duckdb", "polars"] | None = None
    self._polars_lazy_frame: pl.LazyFrame | None = None

  def close(self) -> None:
    """Close the underlying DuckDB database connection."""
    self._connection.close()

  def inspect_and_load_source(
    self,
    path: Path | str,
    *,
    execution_mode: Literal["eager", "lazy"] = "eager",
    lazy_engine: Literal["duckdb", "polars"] | None = None,
    delimiter: str | None = None,
    has_header: bool | None = None,
  ) -> DatasetInfo:
    """Inspect data schema from file path and load content.

    Sets up active eager tables or lazy frame references.

    Args:
      path: File path or remote URI.
      execution_mode: Engine loading strategy, either 'eager' or 'lazy'.
      lazy_engine: Target query pushdown engine ('duckdb' or 'polars').
      delimiter: Delimiter to parse CSV columns.
      has_header: Explicit header configuration override for CSV files.

    Returns:
      A DatasetInfo object describing the schema, dimensions, and execution spec.

    Raises:
      ExecutionError: If parameters are invalid, formats are mismatched, or loading fails.
    """
    source = resolve_load_source(path)

    if source.format != "csv" and (delimiter is not None or has_header is not None):
      raise ExecutionError("options delimiter and has_header are only supported for CSV files")

    if execution_mode == "lazy" and not lazy_mode_supported(source.format):
      raise ExecutionError("use lazy mode only supports Parquet files")

    try:
      if source.format == "stata":
        import os

        if source.is_remote:
          import urllib.request

          try:
            req = urllib.request.Request(source.read_path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
              with tempfile.NamedTemporaryFile(suffix=".dta", delete=False) as tmp_file:
                tmp_file.write(response.read())
                temp_path = tmp_file.name
            frame = pd.read_stata(temp_path)
            try:
              os.unlink(temp_path)
            except OSError:
              pass
          except Exception as exc:
            message = f"use could not read Stata file: {source.read_path}"
            raise ExecutionError(message) from exc
        else:
          frame = pd.read_stata(source.read_path)
        stage_name = "__tabdat_stata_source"
        self._connection.register(stage_name, frame)
        try:
          stage_identifier = _quote_identifier(stage_name)
          self._connection.execute(
            f"create or replace temp table {NEXT_ACTIVE_TABLE} as select * from {stage_identifier}"
          )
        finally:
          self._connection.unregister(stage_name)
        self._drop_active_relation()
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._lazy_engine = None
        self._active_storage = "table"
        self._polars_lazy_frame = None
        return self.active_dataset_info(source.display_path)

      elif source.format in {"feather", "arrow"}:
        import os

        if source.is_remote:
          import urllib.request

          try:
            req = urllib.request.Request(source.read_path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
              with tempfile.NamedTemporaryFile(
                suffix=f".{source.format}", delete=False
              ) as tmp_file:
                tmp_file.write(response.read())
                temp_path = tmp_file.name
            import pyarrow.feather as pf

            table = pf.read_table(temp_path)
            try:
              os.unlink(temp_path)
            except OSError:
              pass
          except Exception as exc:
            raise ExecutionError(
              f"use could not read {source.format.upper()} file: {source.read_path}"
            ) from exc
        else:
          import pyarrow.feather as pf

          table = pf.read_table(source.read_path)

        stage_name = f"__tabdat_{source.format}_source"
        self._connection.register(stage_name, table)
        try:
          stage_identifier = _quote_identifier(stage_name)
          self._connection.execute(
            f"create or replace temp table {NEXT_ACTIVE_TABLE} as select * from {stage_identifier}"
          )
        finally:
          self._connection.unregister(stage_name)
        self._drop_active_relation()
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._lazy_engine = None
        self._active_storage = "table"
        self._polars_lazy_frame = None
        return self.active_dataset_info(source.display_path)

      elif source.format == "csv":
        import os

        if source.is_remote:
          import urllib.request

          try:
            req = urllib.request.Request(source.read_path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
              with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
                tmp_file.write(response.read())
                temp_path = tmp_file.name
            csv_read_path = temp_path
          except Exception as exc:
            raise ExecutionError(f"use could not read CSV file: {source.read_path}") from exc
        else:
          csv_read_path = source.read_path

        try:
          options_sql = []
          args: list[str | bool] = [csv_read_path]
          if delimiter is not None:
            options_sql.append("delim=?")
            args.append(delimiter)
          if has_header is not None:
            options_sql.append("header=?")
            args.append(has_header)

          options_str = f", {', '.join(options_sql)}" if options_sql else ""
          self._connection.execute(
            f"create or replace temp table {NEXT_ACTIVE_TABLE} "
            f"as select * from read_csv_auto(?{options_str})",
            args,
          )
        finally:
          if source.is_remote:
            try:
              os.unlink(csv_read_path)
            except OSError:
              pass

        self._drop_active_relation()
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._lazy_engine = None
        self._active_storage = "table"
        self._polars_lazy_frame = None
        return self.active_dataset_info(source.display_path)

      elif execution_mode == "lazy" and lazy_engine == "polars":
        if not lazy_engine_supported(source.format, "polars", is_remote=source.is_remote):
          raise ExecutionError("use lazy engine=polars only supports local Parquet paths")
        next_lazy_frame = pl.scan_parquet(str(source.display_path))
        schema = next_lazy_frame.collect_schema()
        columns = tuple(
          ColumnInfo(name=name, data_type=_polars_dtype_name(dtype))
          for name, dtype in schema.items()
        )
        self._drop_active_relation()
        self._polars_lazy_frame = next_lazy_frame
        self._lazy_engine = "polars"
        self._active_storage = "view"
        return DatasetInfo(
          path=source.display_path,
          row_count=None,
          columns=columns,
          execution_mode="lazy",
          lazy_engine="polars",
        )
      if execution_mode == "lazy":
        read_sql = f"select * from read_parquet({_quote_literal(source.read_path)})"
        self._connection.execute(
          f"create or replace temp view {NEXT_ACTIVE_VIEW} as {read_sql}",
        )
        self._drop_active_relation()
        self._connection.execute(f"create or replace temp view {ACTIVE_TABLE} as {read_sql}")
        self._connection.execute(f"drop view {NEXT_ACTIVE_VIEW}")
        self._lazy_engine = lazy_engine
        self._active_storage = "view"
      else:
        self._connection.execute(
          f"create or replace temp table {NEXT_ACTIVE_TABLE} as select * from read_parquet(?)",
          [source.read_path],
        )
        self._drop_active_relation()
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._lazy_engine = None
        self._active_storage = "table"
        self._polars_lazy_frame = None
    except duckdb.Error as exc:
      self._drop_load_staging_relations()
      message = f"use could not read {source.format.title()} file: {source.read_path}"
      raise ExecutionError(message) from exc
    except (PolarsError, OSError, URLError, ValueError) as exc:
      message = f"use could not read {source.format.title()} file: {source.read_path}"
      raise ExecutionError(message) from exc

    return self.active_dataset_info(source.display_path)

  def active_dataset_info(self, path: Path | str) -> DatasetInfo:
    if self._polars_lazy_frame is not None:
      try:
        schema = self._polars_lazy_frame.collect_schema()
      except PolarsError as exc:
        raise ExecutionError("active dataset is not available") from exc
      columns = tuple(
        ColumnInfo(name=name, data_type=_polars_dtype_name(dtype)) for name, dtype in schema.items()
      )
      return DatasetInfo(
        path=path,
        row_count=None,
        columns=columns,
        execution_mode="lazy",
        lazy_engine="polars",
      )
    try:
      description = self._connection.execute(f"describe {ACTIVE_TABLE}").fetchall()
    except duckdb.Error as exc:
      raise ExecutionError("active dataset is not available") from exc
    columns = tuple(ColumnInfo(name=row[0], data_type=row[1]) for row in description)
    row_count = None if self._active_storage == "view" else self.active_row_count()
    return DatasetInfo(
      path=path,
      row_count=row_count,
      columns=columns,
      execution_mode="lazy" if self._active_storage == "view" else "eager",
      lazy_engine=self._lazy_engine,
    )

  def active_row_count(self) -> int:
    if self._polars_lazy_frame is not None:
      return self._polars_row_count()
    try:
      row_count_row = self._connection.execute(f"select count(*) from {ACTIVE_TABLE}").fetchone()
    except duckdb.Error as exc:
      raise ExecutionError("count failed") from exc
    if row_count_row is None:
      raise ExecutionError("count failed")
    return cast(int, row_count_row[0])

  def create_named_table_from_sql(
    self,
    dataset: DatasetInfo,
    query: str,
    table_name: str,
  ) -> DatasetInfo:
    if self._polars_lazy_frame is not None:
      self.materialize_polars_lazy(dataset.path)
    _validate_user_table_name(table_name)
    _require_result_query(query)
    self._bind_active_view()
    internal_name = _named_table_identifier(table_name)
    try:
      self._connection.execute(
        f"create or replace temp table {_quote_identifier(internal_name)} as {query}"
      )
    except duckdb.Error as exc:
      raise BackendExecutionError("sql failed") from exc
    self._activate_relation(internal_name, "sql")
    return self.active_dataset_info(Path(table_name))

  def activate_named_table(self, table_name: str) -> DatasetInfo:
    _validate_user_table_name(table_name)
    self._polars_lazy_frame = None
    internal_name = _named_table_identifier(table_name)
    self._activate_relation(internal_name, "use")
    return self.active_dataset_info(Path(table_name))

  def store_active_as_named_table(self, table_name: str) -> DatasetInfo:
    if self._polars_lazy_frame is not None:
      self.materialize_polars_lazy(Path(table_name))
    _validate_user_table_name(table_name)
    internal_name = _named_table_identifier(table_name)
    try:
      self._connection.execute(
        f"create or replace temp table {_quote_identifier(internal_name)} as "
        f"select * from {ACTIVE_TABLE}"
      )
    except duckdb.Error as exc:
      raise BackendExecutionError(f"could not update table: {table_name}") from exc
    return self.active_dataset_info(Path(table_name))

  def join_named_table(
    self,
    dataset: DatasetInfo,
    right_dataset: DatasetInfo,
    *,
    table_name: str,
    keys: tuple[str, ...],
    how: Literal["inner", "left"],
    suffix: str,
  ) -> DatasetInfo:
    _validate_user_table_name(table_name)
    left_types = {column.name: column.data_type for column in dataset.columns}
    right_types = {column.name: column.data_type for column in right_dataset.columns}
    _require_columns("join", left_types, keys)
    missing_right = tuple(key for key in keys if key not in right_types)
    if missing_right:
      raise UnknownVariableError(
        f"join unknown variable in {table_name}: {', '.join(missing_right)}"
      )

    internal_name = _named_table_identifier(table_name)
    right_selects = _right_join_selects(right_dataset, keys, left_types, suffix)
    select_sql = ", ".join(
      f"left_table.{_quote_identifier(column.name)}" for column in dataset.columns
    )
    if right_selects:
      select_sql = f"{select_sql}, {', '.join(right_selects)}"
    predicates = " and ".join(
      f"left_table.{_quote_identifier(key)} = right_table.{_quote_identifier(key)}" for key in keys
    )
    self._replace_active(
      f"""
      select {select_sql}
      from (
        select row_number() over () as __tabdat_join_order, *
        from {ACTIVE_TABLE}
      ) as left_table
      {how} join (
        select row_number() over () as __tabdat_join_order, *
        from {_quote_identifier(internal_name)}
      ) as right_table
        on {predicates}
      order by left_table.__tabdat_join_order, right_table.__tabdat_join_order
      """,
      "join",
    )
    return self.active_dataset_info(dataset.path)

  def append_named_table(
    self,
    dataset: DatasetInfo,
    append_dataset: DatasetInfo,
    *,
    table_name: str,
  ) -> DatasetInfo:
    self.validate_append(dataset, append_dataset, table_name=table_name)

    internal_name = _named_table_identifier(table_name)
    select_sql = _select_list(tuple(column.name for column in dataset.columns))
    # Snapshot each input sequence before UNION ALL so the combine cannot interleave rows.
    self._replace_active(
      f"""
      select * exclude (__tabdat_append_side, __tabdat_append_row)
      from (
        select
          0 as __tabdat_append_side,
          row_number() over () as __tabdat_append_row,
          {select_sql}
        from {ACTIVE_TABLE}
        union all
        select
          1 as __tabdat_append_side,
          row_number() over () as __tabdat_append_row,
          {select_sql}
        from {_quote_identifier(internal_name)}
      ) as append_rows
      order by __tabdat_append_side, __tabdat_append_row
      """,
      "append",
    )
    return self.active_dataset_info(dataset.path)

  def validate_append(
    self,
    dataset: DatasetInfo,
    append_dataset: DatasetInfo,
    *,
    table_name: str,
  ) -> None:
    _validate_user_table_name(table_name)
    left_types = {column.name: _canonical_data_type(column.data_type) for column in dataset.columns}
    right_types = {
      column.name: _canonical_data_type(column.data_type) for column in append_dataset.columns
    }
    _require_columns("append", left_types, tuple(right_types))
    missing_right = tuple(
      column.name for column in dataset.columns if column.name not in right_types
    )
    if missing_right:
      raise UnknownVariableError(
        f"append unknown variable in {table_name}: {', '.join(missing_right)}"
      )
    _require_matching_types("append", left_types, right_types, tuple(left_types))

  def reshape_long(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    identifiers: tuple[str, ...],
    j_variable: str,
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("reshape", column_types, identifiers)
    _reject_existing_column("reshape", column_types, j_variable)
    j_values = _long_j_values(dataset, variables)
    for variable in variables:
      _require_long_stub_columns(column_types, variable, j_values)

    id_sql = _select_list(identifiers)
    selects = []
    for j_value in j_values:
      value_sql = ", ".join(
        f"{_quote_identifier(variable + '_' + j_value)} as {_quote_identifier(variable)}"
        for variable in variables
      )
      selects.append(
        f"""
        select {id_sql}, {_quote_literal(j_value)} as {_quote_identifier(j_variable)}, {value_sql}
        from {ACTIVE_TABLE}
        """
      )
    order_sql = ", ".join(_quote_identifier(identifier) for identifier in identifiers)
    self._replace_active(
      f"""
      select *
      from (
        {" union all ".join(selects)}
      )
      order by {order_sql}, {_quote_identifier(j_variable)}
      """,
      "reshape",
    )
    return self.active_dataset_info(dataset.path)

  def reshape_wide(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    identifiers: tuple[str, ...],
    j_variable: str,
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("reshape", column_types, identifiers + (j_variable,) + variables)
    j_values = self._wide_j_values(j_variable)
    if not j_values:
      raise ExecutionError("reshape wide found no j values")
    _require_wide_output_names(column_types, variables, identifiers, j_variable, j_values)

    id_sql = _select_list(identifiers)
    aggregate_sql = ", ".join(
      f"max(case when cast({_quote_identifier(j_variable)} as varchar) = {_quote_literal(j_value)} "
      f"then {_quote_identifier(variable)} end) as {_quote_identifier(variable + '_' + j_value)}"
      for variable in variables
      for j_value in j_values
    )
    self._replace_active(
      f"""
      select {id_sql}, {aggregate_sql}
      from {ACTIVE_TABLE}
      group by {id_sql}
      order by {id_sql}
      """,
      "reshape",
    )
    return self.active_dataset_info(dataset.path)

  def validate_panel_metadata(self, dataset: DatasetInfo, metadata: PanelMetadata) -> None:
    column_types = {column.name: column.data_type for column in dataset.columns}
    variables = (metadata.id_variable, metadata.time_variable)
    _require_columns("panel", column_types, variables)
    missing_variables = tuple(variable for variable in variables if self._has_nulls(variable))
    if missing_variables:
      raise ExecutionError(
        f"panel variables cannot contain missing values: {', '.join(missing_variables)}"
      )
    if self._has_duplicate_panel_pairs(metadata):
      raise ExecutionError("panel id/time pairs must be unique")

  def panel_structure_summary(self, metadata: PanelMetadata) -> PanelStructureSummary:
    id_sql = _quote_identifier(metadata.id_variable)
    time_sql = _quote_identifier(metadata.time_variable)
    summary_sql = f"""
      with entity_counts as (
        select count(*) as obs_count
        from {ACTIVE_TABLE}
        group by {id_sql}
      )
      select
        cast((select count(*) from {ACTIVE_TABLE}) as bigint) as observation_count,
        cast((select count(distinct {id_sql}) from {ACTIVE_TABLE}) as bigint) as entity_count,
        cast((select count(distinct {time_sql}) from {ACTIVE_TABLE}) as bigint) as time_count,
        cast(coalesce(min(obs_count), 0) as bigint) as min_observations_per_entity,
        cast(coalesce(max(obs_count), 0) as bigint) as max_observations_per_entity
      from entity_counts
    """
    row = self._fetch_one(summary_sql, "panel")
    return PanelStructureSummary(
      observation_count=cast(int, row[0]),
      entity_count=cast(int, row[1]),
      time_count=cast(int, row[2]),
      min_observations_per_entity=cast(int, row[3]),
      max_observations_per_entity=cast(int, row[4]),
    )

  def save_active_parquet(self, path: Path, *, replace: bool) -> None:
    normalized = path.expanduser()
    if normalized.suffix.lower() != ".parquet":
      raise ExecutionError("save only supports .parquet files in Phase 9")
    _prepare_output_path(normalized, path, replace=replace, command_name="save")
    if self._polars_lazy_frame is not None:
      frame = self._collect_polars_frame("save", path)
      try:
        frame.write_parquet(normalized)
      except (PolarsError, OSError) as exc:
        raise ExecutionError(f"save failed: {path}") from exc
      return
    try:
      self._connection.execute(
        f"copy (select * from {ACTIVE_TABLE}) to ? (format parquet)",
        [str(normalized)],
      )
    except duckdb.Error as exc:
      raise ExecutionError(f"save failed: {path}") from exc

  def export_active_dataset(self, path: Path, *, replace: bool) -> None:
    normalized = path.expanduser()
    suffix = normalized.suffix.lower()
    if suffix not in {".parquet", ".csv", ".feather"}:
      raise ExecutionError("export only supports .parquet, .csv, and .feather files")
    _prepare_output_path(normalized, path, replace=replace, command_name="export")
    if suffix == ".parquet":
      self.save_active_parquet(path, replace=replace)
      return

    frame = self._active_frame_for_export(command_name="export", path=path)
    try:
      if suffix == ".csv":
        frame.write_csv(normalized)
      else:
        frame.write_ipc(normalized)
    except (PolarsError, OSError) as exc:
      raise ExecutionError(f"export failed: {path}") from exc

  def run_sql(self, query: str) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
    _require_result_query(query)
    self._bind_active_view()
    try:
      result = self._connection.execute(query)
      headers = tuple(column[0] for column in result.description or ())
      rows = tuple(result.fetchall())
    except duckdb.Error as exc:
      raise ExecutionError("sql failed") from exc
    if not headers:
      raise ExecutionError("sql must produce a table result")
    return headers, rows

  def replace_active_with_sql(self, dataset: DatasetInfo, query: str) -> DatasetInfo:
    _require_result_query(query)
    self._bind_active_view()
    self._replace_active(query, "sql")
    return self.active_dataset_info(dataset.path)

  def summarize(self, dataset: DatasetInfo, variables: tuple[str, ...]) -> tuple[SummaryRow, ...]:
    column_types = {column.name: column.data_type.upper() for column in dataset.columns}
    requested = variables or tuple(
      column.name for column in dataset.columns if _is_numeric_type(column.data_type)
    )

    if not requested:
      raise ExecutionError("summarize found no numeric columns")

    _require_columns("summarize", column_types, requested)
    non_numeric = tuple(
      variable for variable in requested if not _is_numeric_type(column_types[variable])
    )
    if non_numeric:
      raise TypeMismatchExecutionError(
        f"summarize requires numeric variables: {', '.join(non_numeric)}"
      )

    return tuple(self._summarize_variable(variable) for variable in requested)

  def grouped_summarize(
    self,
    dataset: DatasetInfo,
    groups: tuple[str, ...],
    variables: tuple[str, ...],
  ) -> tuple[tuple[object, ...], ...]:
    column_types = {column.name: column.data_type.upper() for column in dataset.columns}
    _require_columns("by", column_types, groups)
    requested = variables or tuple(
      column.name
      for column in dataset.columns
      if column.name not in groups and _is_numeric_type(column.data_type)
    )
    if not requested:
      raise ExecutionError("by summarize found no numeric columns")
    _require_columns("summarize", column_types, requested)

    non_numeric = tuple(
      variable for variable in requested if not _is_numeric_type(column_types[variable])
    )
    if non_numeric:
      raise TypeMismatchExecutionError(
        f"summarize requires numeric variables: {', '.join(non_numeric)}"
      )

    group_sql = ", ".join(_quote_identifier(group) for group in groups)
    aggregate_sql = ", ".join(
      f"avg({_quote_identifier(variable)}) as {_quote_identifier('mean_' + variable)}"
      for variable in requested
    )
    sql = f"""
      select {group_sql}, {aggregate_sql}
      from {ACTIVE_TABLE}
      group by {group_sql}
      order by {group_sql}
    """
    return self._fetch_table(sql, "by summarize")

  def grouped_count(
    self,
    dataset: DatasetInfo,
    groups: tuple[str, ...],
  ) -> tuple[tuple[object, ...], ...]:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("by", column_types, groups)
    group_sql = ", ".join(_quote_identifier(group) for group in groups)
    sql = f"""
      select {group_sql}, count(*) as count
      from {ACTIVE_TABLE}
      group by {group_sql}
      order by {group_sql}
    """
    return self._fetch_table(sql, "by count")

  def codebook(self, dataset: DatasetInfo, variables: tuple[str, ...]) -> tuple[CodebookRow, ...]:
    column_types = {column.name: column.data_type for column in dataset.columns}
    requested = variables or tuple(column.name for column in dataset.columns)
    _require_columns("codebook", column_types, requested)

    return tuple(
      self._codebook_variable(variable, column_types[variable]) for variable in requested
    )

  def preview_rows(
    self,
    limit: int,
    *,
    tail: bool = False,
  ) -> tuple[tuple[object, ...], ...]:
    if self._polars_lazy_frame is not None:
      return self._preview_polars_rows(limit, tail=tail)
    if limit == 0:
      return ()

    query = f"""
      select * exclude (__tabdat_row_number)
      from (
        select
          row_number() over () as __tabdat_row_number,
          *
        from {ACTIVE_TABLE}
      )
      order by __tabdat_row_number {"desc" if tail else ""}
      limit ?
    """
    try:
      rows = tuple(self._connection.execute(query, [limit]).fetchall())
    except duckdb.Error as exc:
      command_name = "tail" if tail else "head"
      raise ExecutionError(f"{command_name} failed") from exc

    if tail:
      return tuple(reversed(rows))
    return rows

  def keep_columns(self, dataset: DatasetInfo, variables: tuple[str, ...]) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("keep", column_types, variables)
    if self._polars_lazy_frame is not None:
      self._polars_lazy_frame = self._polars_lazy_frame.select(list(variables))
      return self.active_dataset_info(dataset.path)
    self._replace_active(
      f"select {_select_list(variables)} from {ACTIVE_TABLE}",
      "keep",
    )
    return self.active_dataset_info(dataset.path)

  def drop_columns(self, dataset: DatasetInfo, variables: tuple[str, ...]) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("drop", column_types, variables)
    remaining = tuple(column.name for column in dataset.columns if column.name not in variables)
    if not remaining:
      raise ExecutionError("drop would remove every column")
    if self._polars_lazy_frame is not None:
      self._polars_lazy_frame = self._polars_lazy_frame.select(list(remaining))
      return self.active_dataset_info(dataset.path)
    self._replace_active(
      f"select {_select_list(remaining)} from {ACTIVE_TABLE}",
      "drop",
    )
    return self.active_dataset_info(dataset.path)

  def filter_rows(
    self,
    dataset: DatasetInfo,
    condition: Expression,
    *,
    keep: bool,
  ) -> DatasetInfo:
    self.validate_predicate(dataset, condition)
    if self._polars_lazy_frame is not None:
      condition_expr = self._compile_polars_expression(dataset, condition)
      boolean_condition = condition_expr.fill_null(False)
      polars_predicate = boolean_condition if keep else ~boolean_condition
      self._polars_lazy_frame = self._polars_lazy_frame.filter(polars_predicate)
      return self.active_dataset_info(dataset.path)
    condition_sql = self._compile_expression(dataset, condition)
    sql_predicate: str = (
      condition_sql if keep else f"(not ({condition_sql})) or ({condition_sql}) is null"
    )
    command_name = "keep" if keep else "drop"
    self._replace_active(
      f"""
      select * exclude (__tabdat_row_number)
      from (
        select row_number() over () as __tabdat_row_number, *
        from {ACTIVE_TABLE}
      )
      where {sql_predicate}
      order by __tabdat_row_number
      """,
      command_name,
    )
    return self.active_dataset_info(dataset.path)

  def rename_column(self, dataset: DatasetInfo, old_name: str, new_name: str) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("rename", column_types, (old_name,))
    if new_name in column_types:
      raise ExecutionError(f"rename target already exists: {new_name}")
    renamed = tuple(
      new_name if column.name == old_name else column.name for column in dataset.columns
    )
    select_sql = ", ".join(
      f"{_quote_identifier(column.name)} as {_quote_identifier(new_name)}"
      if column.name == old_name
      else _quote_identifier(column.name)
      for column in dataset.columns
    )
    self._replace_active(f"select {select_sql} from {ACTIVE_TABLE}", "rename")
    next_dataset = self.active_dataset_info(dataset.path)
    if tuple(column.name for column in next_dataset.columns) != renamed:
      raise ExecutionError("rename failed")
    return next_dataset

  def generate_column(
    self,
    dataset: DatasetInfo,
    variable: str,
    expression: Expression,
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    if variable in column_types:
      raise ExecutionError(f"generate target already exists: {variable}")
    expression_sql = self._compile_expression(dataset, expression)
    self._replace_active(
      f"select *, {expression_sql} as {_quote_identifier(variable)} from {ACTIVE_TABLE}",
      "generate",
    )
    return self.active_dataset_info(dataset.path)

  def replace_column(
    self,
    dataset: DatasetInfo,
    variable: str,
    expression: Expression,
    condition: Expression | None,
  ) -> DatasetInfo:
    self.validate_replace(dataset, variable, expression, condition)
    column_types = {column.name: column.data_type for column in dataset.columns}
    expression_sql = self._compile_expression(dataset, expression)
    if isinstance(expression, NullExpression):
      expression_sql = f"cast(NULL as {_null_cast_type(column_types[variable])})"
    replacement_sql = expression_sql
    if condition is not None:
      condition_sql = self._compile_expression(dataset, condition)
      quoted_variable = _quote_identifier(variable)
      replacement_sql = (
        f"case when {condition_sql} then {expression_sql} else {quoted_variable} end"
      )
    select_sql = ", ".join(
      f"{replacement_sql} as {_quote_identifier(column.name)}"
      if column.name == variable
      else _quote_identifier(column.name)
      for column in dataset.columns
    )
    self._replace_active(f"select {select_sql} from {ACTIVE_TABLE}", "replace")
    return self.active_dataset_info(dataset.path)

  def recode_variables(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    rules: tuple[RecodeRule, ...],
    generate_variables: tuple[str, ...] | None,
    replace: bool,
  ) -> DatasetInfo:
    recode_map = {}
    var_targets = list(generate_variables) if generate_variables is not None else list(variables)

    for src_var, target_var in zip(variables, var_targets):
      src_col_info = next(col for col in dataset.columns if col.name == src_var)
      col_type = src_col_info.data_type
      col_ident = _quote_identifier(src_var)

      upper_col_type = col_type.upper()
      is_src_num = any(upper_col_type.startswith(nt) for nt in NUMERIC_TYPES)
      any_string_output = any(isinstance(rule.output, str) for rule in rules)
      to_string_column = any_string_output or not is_src_num

      def format_literal(val):
        if to_string_column:
          return _quote_literal(str(val))
        if isinstance(val, (int, float)):
          return str(val)
        elif isinstance(val, str):
          return _quote_literal(val)
        else:
          return _quote_literal(str(val))

      case_clauses = []
      has_else = False
      else_val = None

      for rule in rules:
        if "else" in rule.inputs:
          has_else = True
          else_val = format_literal(rule.output)
          continue

        conditions = []
        for inp in rule.inputs:
          if isinstance(inp, RecodeRange):
            upper_col_type = col_type.upper()
            is_num = any(upper_col_type.startswith(nt) for nt in NUMERIC_TYPES)
            if not is_num:
              raise ExecutionError(
                f"range recode rule not allowed on non-numeric column: {src_var}"
              )

            if inp.start == "min" and inp.end == "max":
              conditions.append(f"{col_ident} IS NOT NULL")
            elif inp.start == "min":
              conditions.append(f"{col_ident} <= {format_literal(inp.end)}")
            elif inp.end == "max":
              conditions.append(f"{col_ident} >= {format_literal(inp.start)}")
            else:
              conditions.append(
                f"{col_ident} >= {format_literal(inp.start)} "
                f"AND {col_ident} <= {format_literal(inp.end)}"
              )
          elif inp == "missing":
            conditions.append(f"{col_ident} IS NULL")
          elif inp == "nonmissing":
            conditions.append(f"{col_ident} IS NOT NULL")
          else:
            conditions.append(f"{col_ident} = {format_literal(inp)}")

        if conditions:
          or_cond = f"({') OR ('.join(conditions)})" if len(conditions) > 1 else conditions[0]
          case_clauses.append(f"WHEN {or_cond} THEN {format_literal(rule.output)}")

      if to_string_column:
        fallback_sql = f"CAST({col_ident} AS VARCHAR)"
      else:
        fallback_sql = col_ident

      if has_else:
        final_fallback = else_val
      else:
        final_fallback = fallback_sql

      case_sql = f"CASE {' '.join(case_clauses)} ELSE {final_fallback} END"
      recode_map[target_var] = case_sql

    select_items = []
    existing_cols = [col.name for col in dataset.columns]

    if replace:
      for col in existing_cols:
        if col in recode_map:
          select_items.append(f"{recode_map[col]} as {_quote_identifier(col)}")
        else:
          select_items.append(_quote_identifier(col))
    else:
      for col in existing_cols:
        select_items.append(_quote_identifier(col))
      for gen_var in var_targets:
        select_items.append(f"{recode_map[gen_var]} as {_quote_identifier(gen_var)}")

    select_sql = ", ".join(select_items)
    self._replace_active(f"select {select_sql} from {ACTIVE_TABLE}", "recode")
    return self.active_dataset_info(dataset.path)

  def replace_column_with_panel_validation(
    self,
    dataset: DatasetInfo,
    variable: str,
    expression: Expression,
    condition: Expression | None,
    metadata: PanelMetadata,
  ) -> DatasetInfo:
    try:
      self._connection.execute("begin transaction")
      next_dataset = self.replace_column(dataset, variable, expression, condition)
      self.validate_panel_metadata(next_dataset, metadata)
      self._connection.execute("commit")
    except Exception:
      self._rollback_transaction()
      raise
    return next_dataset

  def recode_variables_with_panel_validation(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    rules: tuple[RecodeRule, ...],
    generate_variables: tuple[str, ...] | None,
    replace: bool,
    metadata: PanelMetadata,
  ) -> DatasetInfo:
    try:
      self._connection.execute("begin transaction")
      next_dataset = self.recode_variables(
        dataset,
        variables=variables,
        rules=rules,
        generate_variables=generate_variables,
        replace=replace,
      )
      self.validate_panel_metadata(next_dataset, metadata)
      self._connection.execute("commit")
    except Exception:
      self._rollback_transaction()
      raise
    return next_dataset

  def xtdata_transform(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    *,
    panel_id_variable: str,
    transform: Literal["within", "between"],
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("xtdata", column_types, (panel_id_variable, *variables))
    partition_sql = _quote_identifier(panel_id_variable)
    select_columns = ", ".join(_quote_identifier(column.name) for column in dataset.columns)
    derived_columns = ", ".join(
      _xtdata_expression(variable, partition_sql, transform=transform) for variable in variables
    )
    self._replace_active(
      f"select {select_columns}, {derived_columns} from {ACTIVE_TABLE}",
      "xtdata",
    )
    return self.active_dataset_info(dataset.path)

  def tabulate(
    self,
    dataset: DatasetInfo,
    row_variables: tuple[str, ...],
    column_variables: tuple[str, ...] = (),
    *,
    condition: Expression | None = None,
    value_variable: str | None = None,
    statistic: Literal["count", "mean", "sum", "min", "max"] | None = None,
    row_percent: bool,
    column_percent: bool,
    include_missing: bool,
    by_variables: tuple[str, ...] = (),
  ) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
    self.validate_tabulate(
      dataset,
      row_variables,
      column_variables,
      condition=condition,
      value_variable=value_variable,
      statistic=statistic,
      by_variables=by_variables,
    )
    long_rows = self._tabulate_long(
      dataset,
      row_variables,
      column_variables,
      condition=condition,
      value_variable=value_variable,
      statistic=statistic,
      row_percent=row_percent,
      column_percent=column_percent,
      include_missing=include_missing,
      by_variables=by_variables,
    )
    if not column_variables:
      if value_variable is None:
        return by_variables + row_variables + ("Count", "Percent"), long_rows
      value_header = statistic or "Value"
      return by_variables + row_variables + (value_header,), long_rows
    return _tabulate_wide_result(
      long_rows,
      by_variables=by_variables,
      row_variables=row_variables,
      column_variables=column_variables,
      include_row_percent=row_percent,
      include_column_percent=column_percent,
      value_header="Count" if value_variable is None else statistic or "Value",
      missing_cell_value=0 if value_variable is None or statistic == "count" else None,
    )

  def validate_tabulate(
    self,
    dataset: DatasetInfo,
    row_variables: tuple[str, ...],
    column_variables: tuple[str, ...] = (),
    *,
    condition: Expression | None = None,
    value_variable: str | None = None,
    statistic: Literal["count", "mean", "sum", "min", "max"] | None = None,
    by_variables: tuple[str, ...] = (),
  ) -> None:
    """Validate tabulate inputs without querying or materializing the active relation."""
    column_types = {column.name: column.data_type for column in dataset.columns}
    dimensions = by_variables + row_variables + column_variables
    _require_columns("tabulate", column_types, dimensions)
    if value_variable is not None:
      _require_columns("tabulate", column_types, (value_variable,))
      if statistic in {"mean", "sum", "min", "max"} and not _is_numeric_type(
        column_types[value_variable]
      ):
        raise TypeMismatchExecutionError(
          f"tabulate {statistic} requires numeric variable: {value_variable}"
        )
    if condition is not None:
      self.validate_predicate(dataset, condition)

  def collapse(
    self,
    dataset: DatasetInfo,
    statistic: str,
    variables: tuple[str, ...],
    groups: tuple[str, ...],
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type.upper() for column in dataset.columns}
    _require_columns("collapse", column_types, groups)
    _require_columns("collapse", column_types, variables)
    if statistic != "count":
      non_numeric = tuple(
        variable for variable in variables if not _is_numeric_type(column_types[variable])
      )
      if non_numeric:
        raise TypeMismatchExecutionError(
          f"collapse {statistic} requires numeric variables: {', '.join(non_numeric)}"
        )

    group_sql = ", ".join(_quote_identifier(group) for group in groups)
    aggregate_sql = ", ".join(
      f"{statistic}({_quote_identifier(variable)}) "
      f"as {_quote_identifier(statistic + '_' + variable)}"
      for variable in variables
    )
    self._replace_active(
      f"""
      select {group_sql}, {aggregate_sql}
      from {ACTIVE_TABLE}
      group by {group_sql}
      order by {group_sql}
      """,
      "collapse",
    )
    return self.active_dataset_info(dataset.path)

  def plot_rows(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    *,
    numeric: bool,
  ) -> tuple[tuple[object, ...], ...]:
    column_types = {column.name: column.data_type.upper() for column in dataset.columns}
    _require_columns("plot", column_types, variables)
    if numeric:
      non_numeric = tuple(
        variable for variable in variables if not _is_numeric_type(column_types[variable])
      )
      if non_numeric:
        raise TypeMismatchExecutionError(
          f"plot requires numeric variables: {', '.join(non_numeric)}"
        )
    select_sql = _select_list(variables)
    return self._fetch_table(f"select {select_sql} from {ACTIVE_TABLE}", "plot")

  def bar_counts(
    self,
    dataset: DatasetInfo,
    variable: str,
    *,
    include_missing: bool,
  ) -> tuple[tuple[object, ...], ...]:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("bar", column_types, (variable,))
    quoted = _quote_identifier(variable)
    where_sql = "" if include_missing else f"where {quoted} is not null"
    return self._fetch_table(
      f"""
      select cast({quoted} as varchar) as value, count(*) as count
      from {ACTIVE_TABLE}
      {where_sql}
      group by {quoted}
      order by ({quoted} is null), count desc, {quoted} nulls last
      """,
      "bar",
    )

  def regression_rows(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
  ) -> tuple[tuple[object, ...], ...]:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("regress", column_types, variables)
    select_sql = _select_list(variables)
    return self._fetch_table(f"select {select_sql} from {ACTIVE_TABLE}", "regress")

  def add_linear_prediction_column(
    self,
    dataset: DatasetInfo,
    *,
    target_variable: str,
    predictor_names: tuple[str, ...],
    predictor_coefficients: tuple[float, ...],
    intercept: float | None,
    outcome_variable: str,
    kind: Literal["xb", "residuals"],
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    if target_variable in column_types:
      raise ExecutionError(f"predict target already exists: {target_variable}")
    _require_columns("predict", column_types, predictor_names)
    if kind == "residuals":
      _require_columns("predict", column_types, (outcome_variable,))
    prediction_sql = _linear_prediction_sql(
      predictor_names=predictor_names,
      predictor_coefficients=predictor_coefficients,
      intercept=intercept,
    )
    expression_sql = (
      prediction_sql
      if kind == "xb"
      else f"{_quote_identifier(outcome_variable)} - ({prediction_sql})"
    )
    self._replace_active(
      f"select *, {expression_sql} as {_quote_identifier(target_variable)} from {ACTIVE_TABLE}",
      "predict",
    )
    return self.active_dataset_info(dataset.path)

  def add_cf_prediction_column(
    self,
    dataset: DatasetInfo,
    *,
    target_variable: str,
    first_stage_predictor_names: tuple[str, ...],
    first_stage_predictor_coefficients: tuple[float, ...],
    first_stage_intercept: float | None,
    second_stage_predictor_names: tuple[str, ...],
    second_stage_predictor_coefficients: tuple[float, ...],
    second_stage_intercept: float | None,
    second_stage_residual_index: int,
    endogenous_variable: str,
    outcome_variable: str,
    kind: Literal["xb", "residuals"],
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    if target_variable in column_types:
      raise ExecutionError(f"predict target already exists: {target_variable}")
    _require_columns("predict", column_types, first_stage_predictor_names)
    cf_required = tuple(
      name
      for index, name in enumerate(second_stage_predictor_names)
      if index != second_stage_residual_index
    )
    _require_columns("predict", column_types, cf_required)
    if kind == "residuals":
      _require_columns("predict", column_types, (outcome_variable,))
    prediction_sql = _cf_prediction_sql(
      first_stage_predictor_names=first_stage_predictor_names,
      first_stage_predictor_coefficients=first_stage_predictor_coefficients,
      first_stage_intercept=first_stage_intercept,
      second_stage_predictor_names=second_stage_predictor_names,
      second_stage_predictor_coefficients=second_stage_predictor_coefficients,
      second_stage_intercept=second_stage_intercept,
      second_stage_residual_index=second_stage_residual_index,
      endogenous_variable=endogenous_variable,
    )
    expression_sql = (
      prediction_sql
      if kind == "xb"
      else f"{_quote_identifier(outcome_variable)} - ({prediction_sql})"
    )
    self._replace_active(
      f"select *, {expression_sql} as {_quote_identifier(target_variable)} from {ACTIVE_TABLE}",
      "predict",
    )
    return self.active_dataset_info(dataset.path)

  def add_numeric_column_from_values(
    self,
    dataset: DatasetInfo,
    *,
    target_variable: str,
    values: Sequence[float | None],
    command_name: str,
  ) -> DatasetInfo:
    return self.add_numeric_columns_from_values(
      dataset,
      columns=((target_variable, values),),
      command_name=command_name,
    )

  def add_numeric_columns_from_values(
    self,
    dataset: DatasetInfo,
    *,
    columns: Sequence[tuple[str, Sequence[float | None]]],
    command_name: str,
  ) -> DatasetInfo:
    column_types = {column.name: column.data_type for column in dataset.columns}
    target_variables = tuple(name for name, _values in columns)
    if not target_variables:
      raise ExecutionError(f"{command_name} failed")
    seen_targets: set[str] = set()
    for target_variable in target_variables:
      if target_variable in column_types or target_variable in seen_targets:
        raise ExecutionError(f"{command_name} target already exists: {target_variable}")
      seen_targets.add(target_variable)
    expected_count = self.active_row_count()
    for _target_variable, values in columns:
      if expected_count != len(values):
        raise ExecutionError(f"{command_name} failed")
    row_table = "__tabdat_pred_rows"
    value_table = "__tabdat_pred_values"
    value_columns = tuple(f"__value_{index}" for index in range(len(columns)))
    value_column_sql = ", ".join(f"{column} double" for column in value_columns)
    insert_placeholders = ", ".join("?" for _ in range(len(columns) + 1))
    selected_values_sql = ",\n          ".join(
      f"values_data.{value_column} as {_quote_identifier(target_variable)}"
      for value_column, target_variable in zip(value_columns, target_variables, strict=True)
    )
    try:
      self._connection.execute(
        f"""
        create or replace temp table {row_table} as
        select row_number() over () as __row_id, * from {ACTIVE_TABLE}
        """
      )
      self._connection.execute(
        f"create or replace temp table {value_table} (__row_id bigint, {value_column_sql})"
      )
      self._connection.executemany(
        f"insert into {value_table} values ({insert_placeholders})",
        tuple(
          (index + 1,) + tuple(_nullable_float(values[index]) for _name, values in columns)
          for index in range(expected_count)
        ),
      )
      self._replace_active(
        f"""
        select
          row_data.* exclude (__row_id),
          {selected_values_sql}
        from {row_table} as row_data
        inner join {value_table} as values_data
        on row_data.__row_id = values_data.__row_id
        order by row_data.__row_id
        """,
        command_name,
      )
      self._connection.execute(f"drop table if exists {row_table}")
      self._connection.execute(f"drop table if exists {value_table}")
    except duckdb.Error as exc:
      raise ExecutionError(f"{command_name} failed") from exc
    return self.active_dataset_info(dataset.path)

  def _summarize_variable(self, variable: str) -> SummaryRow:
    quoted_variable = _quote_identifier(variable)
    sql = f"""
      select
        count({quoted_variable}) as count,
        avg({quoted_variable}) as mean,
        stddev_samp({quoted_variable}) as std_dev,
        min({quoted_variable}) as minimum,
        max({quoted_variable}) as maximum
      from {ACTIVE_TABLE}
    """
    try:
      row = self._connection.execute(sql).fetchone()
    except duckdb.Error as exc:
      raise ExecutionError(f"summarize failed for variable: {variable}") from exc
    if row is None:
      raise ExecutionError(f"summarize failed for variable: {variable}")
    count, mean, std_dev, minimum, maximum = row

    return SummaryRow(
      variable=variable,
      count=count,
      mean=mean,
      std_dev=std_dev,
      minimum=minimum,
      maximum=maximum,
    )

  def _codebook_variable(self, variable: str, data_type: str) -> CodebookRow:
    quoted_variable = _quote_identifier(variable)
    profile_sql = f"""
      select
        count({quoted_variable}) as nonmissing,
        count(*) - count({quoted_variable}) as missing,
        count(distinct {quoted_variable}) as distinct_count
      from {ACTIVE_TABLE}
    """
    examples_sql = f"""
      select {quoted_variable}
      from {ACTIVE_TABLE}
      where {quoted_variable} is not null
      limit 3
    """
    try:
      profile_row = self._connection.execute(profile_sql).fetchone()
      examples = tuple(row[0] for row in self._connection.execute(examples_sql).fetchall())
    except duckdb.Error as exc:
      raise ExecutionError(f"codebook failed for variable: {variable}") from exc
    if profile_row is None:
      raise ExecutionError(f"codebook failed for variable: {variable}")
    nonmissing, missing, distinct = profile_row

    return CodebookRow(
      variable=variable,
      data_type=data_type,
      nonmissing=nonmissing,
      missing=missing,
      distinct=distinct,
      examples=examples,
    )

  def _tabulate_long(
    self,
    dataset: DatasetInfo,
    row_variables: tuple[str, ...],
    column_variables: tuple[str, ...],
    *,
    condition: Expression | None,
    value_variable: str | None,
    statistic: Literal["count", "mean", "sum", "min", "max"] | None,
    row_percent: bool,
    column_percent: bool,
    include_missing: bool,
    by_variables: tuple[str, ...],
  ) -> tuple[tuple[object, ...], ...]:
    dimensions = by_variables + row_variables + column_variables
    select_dimensions = _select_alias_sql(dimensions)
    group_dimensions = _group_alias_sql(dimensions)
    order_dimensions = _order_alias_sql(dimensions)
    predicates = _tabulate_predicates(
      dataset,
      dimensions,
      condition=condition,
      value_variable=value_variable,
      include_missing=include_missing,
      compile_expression=self._compile_expression,
    )
    where_sql = "" if not predicates else f"where {' and '.join(predicates)}"
    aggregate_sql = _tabulate_aggregate_sql(value_variable, statistic)
    if not column_variables:
      if value_variable is None:
        percent_partition = _partition_alias_sql(tuple(range(0, len(by_variables))))
        sql = f"""
          with cells as (
            select {select_dimensions}, {aggregate_sql} as cell_value
            from {ACTIVE_TABLE}
            {where_sql}
            group by {group_dimensions}
          )
          select
            {group_dimensions},
            cell_value,
            100.0 * cell_value / sum(cell_value) over (partition by {percent_partition})
              as percent
          from cells
          order by {order_dimensions}
        """
        return self._fetch_table(sql, "tabulate")
      sql = f"""
        select {select_dimensions}, {aggregate_sql} as cell_value
        from {ACTIVE_TABLE}
        {where_sql}
        group by {group_dimensions}
        order by {order_dimensions}
      """
      return self._fetch_table(sql, "tabulate")

    row_partition = _partition_alias_sql(tuple(range(0, len(by_variables) + len(row_variables))))
    column_partition = _partition_alias_sql(
      tuple(range(0, len(by_variables)))
      + tuple(
        range(
          len(by_variables) + len(row_variables),
          len(by_variables) + len(row_variables) + len(column_variables),
        )
      )
    )
    extra_columns: list[str] = []
    if row_percent:
      extra_columns.append(
        f"100.0 * cell_value / sum(cell_value) over (partition by {row_partition}) as row_percent"
      )
    if column_percent:
      extra_columns.append(
        f"100.0 * cell_value / sum(cell_value) over (partition by {column_partition}) "
        "as column_percent"
      )
    extra_sql = "" if not extra_columns else ", " + ", ".join(extra_columns)
    sql = f"""
      with cells as (
        select {select_dimensions}, {aggregate_sql} as cell_value
        from {ACTIVE_TABLE}
        {where_sql}
        group by {group_dimensions}
      )
      select {group_dimensions}, cell_value{extra_sql}
      from cells
      order by {order_dimensions}
    """
    return self._fetch_table(sql, "tabulate")

  def _compile_expression(self, dataset: DatasetInfo, expression: Expression) -> str:
    self._infer_expression_domain(dataset, expression)
    if isinstance(expression, BinaryExpression) and expression.operator in {
      "==",
      "!=",
      "<",
      "<=",
      ">",
      ">=",
    }:
      left_is_null = isinstance(expression.left, NullExpression)
      right_is_null = isinstance(expression.right, NullExpression)
      if left_is_null or right_is_null:
        if left_is_null and right_is_null:
          return "TRUE" if expression.operator == "==" else "FALSE"
        other = expression.right if left_is_null else expression.left
        other_sql = self._compile_expression(dataset, other)
        comparator = "is null" if expression.operator == "==" else "is not null"
        return f"({other_sql} {comparator})"
      left = self._compile_expression_operand(dataset, expression.left)
      right = self._compile_expression_operand(dataset, expression.right)
      return f"({left} {expression.operator} {right})"
    if _is_numeric_result_expression(expression):
      return _safe_sql_numeric_result(self._compile_expression_raw(dataset, expression))
    return self._compile_expression_raw(dataset, expression)

  def _compile_expression_operand(self, dataset: DatasetInfo, expression: Expression) -> str:
    if _is_numeric_result_expression(expression):
      return _safe_sql_numeric_result(self._compile_expression_raw(dataset, expression))
    return self._compile_expression_raw(dataset, expression)

  def _compile_expression_raw(self, dataset: DatasetInfo, expression: Expression) -> str:
    column_types = {column.name: column.data_type for column in dataset.columns}
    if isinstance(expression, IdentifierExpression):
      _require_columns("expression", column_types, (expression.name,))
      return _quote_identifier(expression.name)
    if isinstance(expression, NumberExpression):
      return str(expression.value)
    if isinstance(expression, StringExpression):
      return _quote_literal(expression.value)
    if isinstance(expression, NullExpression):
      return "NULL"
    if isinstance(expression, UnaryExpression):
      if _contains_null_literal(expression.operand):
        raise ExecutionError(NULL_LITERAL_ERROR)
      if _has_unsafe_unsigned_arithmetic(column_types, expression):
        raise TypeMismatchExecutionError(UNSIGNED_ARITHMETIC_ERROR)
      operand_sql = self._compile_expression_raw(dataset, expression.operand)
      return f"-({operand_sql})"
    if isinstance(expression, BinaryExpression):
      if _contains_null_literal(expression) and expression.operator not in {"==", "!="}:
        raise ExecutionError(NULL_LITERAL_ERROR)
      if _has_unsafe_unsigned_arithmetic(column_types, expression):
        raise TypeMismatchExecutionError(UNSIGNED_ARITHMETIC_ERROR)
      if _has_unsafe_unsigned_numeric_pair(column_types, expression):
        raise TypeMismatchExecutionError(
          "expression type mismatch: unsigned numeric values cannot be combined with negative "
          "numeric literals"
        )
      left_is_null = isinstance(expression.left, NullExpression)
      right_is_null = isinstance(expression.right, NullExpression)
      if left_is_null or right_is_null:
        if left_is_null and right_is_null:
          return "TRUE" if expression.operator == "==" else "FALSE"
        other = expression.right if left_is_null else expression.left
        other_sql = self._compile_expression_operand(dataset, other)
        comparator = "is null" if expression.operator == "==" else "is not null"
        return f"({other_sql} {comparator})"
      if expression.operator in {"==", "!=", "<", "<=", ">", ">="}:
        left = self._compile_expression_operand(dataset, expression.left)
        right = self._compile_expression_operand(dataset, expression.right)
      else:
        left = self._compile_expression_raw(dataset, expression.left)
        right = self._compile_expression_raw(dataset, expression.right)
      return f"({left} {expression.operator} {right})"
    if isinstance(expression, FunctionCallExpression):
      if _contains_null_literal(expression):
        raise ExecutionError(NULL_LITERAL_ERROR)
      function_name = expression.name.lower()
      if function_name not in SUPPORTED_FUNCTIONS:
        raise ExecutionError(f"unsupported function in expression: {expression.name}")
      arguments = ", ".join(
        self._compile_expression_raw(dataset, argument) for argument in expression.arguments
      )
      return f"{function_name}({arguments})"
    raise ExecutionError("unsupported expression")

  def _compile_polars_expression(self, dataset: DatasetInfo, expression: Expression) -> pl.Expr:
    self._infer_expression_domain(dataset, expression)
    column_types = {column.name: column.data_type for column in dataset.columns}
    if isinstance(expression, IdentifierExpression):
      _require_columns("expression", column_types, (expression.name,))
      return pl.col(expression.name)
    if isinstance(expression, NumberExpression):
      return pl.lit(expression.value)
    if isinstance(expression, StringExpression):
      return pl.lit(expression.value)
    if isinstance(expression, NullExpression):
      return pl.lit(None)
    if isinstance(expression, UnaryExpression):
      if _contains_null_literal(expression.operand):
        raise ExecutionError(NULL_LITERAL_ERROR)
      operand_expr = self._compile_polars_expression(dataset, expression.operand)
      return _normalize_polars_numeric_result(-operand_expr)
    if isinstance(expression, BinaryExpression):
      if _contains_null_literal(expression) and expression.operator not in {"==", "!="}:
        raise ExecutionError(NULL_LITERAL_ERROR)
      left_is_null = isinstance(expression.left, NullExpression)
      right_is_null = isinstance(expression.right, NullExpression)
      if left_is_null or right_is_null:
        if left_is_null and right_is_null:
          return pl.lit(expression.operator == "==")
        other = expression.right if left_is_null else expression.left
        other_expr = self._compile_polars_expression(dataset, other)
        return other_expr.is_null() if expression.operator == "==" else other_expr.is_not_null()
      left = self._compile_polars_expression(dataset, expression.left)
      right = self._compile_polars_expression(dataset, expression.right)
      if expression.operator == "+":
        return _normalize_polars_numeric_result(left + right)
      if expression.operator == "-":
        return _normalize_polars_numeric_result(left - right)
      if expression.operator == "*":
        return _normalize_polars_numeric_result(left * right)
      if expression.operator == "/":
        denominator_is_zero = right == pl.lit(0)
        safe_right = pl.when(denominator_is_zero).then(pl.lit(1)).otherwise(right)
        normalized_division = _normalize_polars_numeric_result(left / safe_right)
        return pl.when(denominator_is_zero).then(pl.lit(None)).otherwise(normalized_division)
      if expression.operator == "==":
        return left == right
      if expression.operator == "!=":
        return left != right
      if expression.operator == "<":
        return left < right
      if expression.operator == "<=":
        return left <= right
      if expression.operator == ">":
        return left > right
      if expression.operator == ">=":
        return left >= right
    if isinstance(expression, FunctionCallExpression):
      if _contains_null_literal(expression):
        raise ExecutionError(NULL_LITERAL_ERROR)
      function_name = expression.name.lower()
      if function_name not in SUPPORTED_FUNCTIONS:
        raise ExecutionError(f"unsupported function in expression: {expression.name}")
      arguments = tuple(
        self._compile_polars_expression(dataset, argument) for argument in expression.arguments
      )
      compiled = _compile_polars_function(function_name, arguments)
      if function_name in NUMERIC_FUNCTIONS:
        return _normalize_polars_numeric_result(compiled)
      return compiled
    raise ExecutionError("unsupported expression")

  def is_polars_lazy_active(self) -> bool:
    return self._polars_lazy_frame is not None

  def validate_expression(self, dataset: DatasetInfo, expression: Expression) -> None:
    """Validate an expression without changing the active relation."""
    self._infer_expression_domain(dataset, expression)
    self._compile_polars_expression(dataset, expression)

  def validate_predicate(self, dataset: DatasetInfo, expression: Expression) -> None:
    """Validate an expression used as a row-selection condition."""
    domain = self._infer_expression_domain(dataset, expression)
    if domain not in {"boolean", "null"}:
      raise TypeMismatchExecutionError("predicate requires boolean expression")

  def validate_replace(
    self,
    dataset: DatasetInfo,
    variable: str,
    expression: Expression,
    condition: Expression | None,
  ) -> None:
    """Validate replacement expression and optional condition before mutation."""
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("replace", column_types, (variable,))
    expression_domain = self._infer_expression_domain(dataset, expression)
    target_domain = _expression_domain_for_data_type(column_types[variable])
    if expression_domain not in {"null", target_domain}:
      raise TypeMismatchExecutionError(
        f"replace target {variable} is {target_domain} but expression is {expression_domain}"
      )
    if condition is not None:
      self.validate_predicate(dataset, condition)

  def _infer_expression_domain(
    self,
    dataset: DatasetInfo,
    expression: Expression,
  ) -> ExpressionDomain:
    column_types = {column.name: column.data_type for column in dataset.columns}
    if isinstance(expression, IdentifierExpression):
      _require_columns("expression", column_types, (expression.name,))
      return _expression_domain_for_data_type(column_types[expression.name])
    if isinstance(expression, NumberExpression):
      return "numeric"
    if isinstance(expression, StringExpression):
      return "string"
    if isinstance(expression, NullExpression):
      return "null"
    if isinstance(expression, UnaryExpression):
      operand_domain = self._infer_expression_domain(dataset, expression.operand)
      if operand_domain == "null":
        raise ExecutionError(NULL_LITERAL_ERROR)
      if _has_unsafe_unsigned_arithmetic(column_types, expression):
        raise TypeMismatchExecutionError(UNSIGNED_ARITHMETIC_ERROR)
      if operand_domain != "numeric":
        raise TypeMismatchExecutionError(
          "expression type mismatch: unary minus requires numeric operand"
        )
      return "numeric"
    if isinstance(expression, BinaryExpression):
      if _contains_null_literal(expression) and expression.operator not in {"==", "!="}:
        raise ExecutionError(NULL_LITERAL_ERROR)
      if _has_unsafe_unsigned_arithmetic(column_types, expression):
        raise TypeMismatchExecutionError(UNSIGNED_ARITHMETIC_ERROR)
      if _has_unsafe_unsigned_numeric_pair(column_types, expression):
        raise TypeMismatchExecutionError(
          "expression type mismatch: unsigned numeric values cannot be combined with negative "
          "numeric literals"
        )
      left_domain = self._infer_expression_domain(dataset, expression.left)
      right_domain = self._infer_expression_domain(dataset, expression.right)
      if expression.operator in {"==", "!=", "<", "<=", ">", ">="}:
        if left_domain == "null" or right_domain == "null":
          if expression.operator not in {"==", "!="}:
            raise ExecutionError(NULL_LITERAL_ERROR)
          return "boolean"
        if left_domain != right_domain and not {
          left_domain,
          right_domain,
        } == {"numeric"}:
          raise TypeMismatchExecutionError(
            f"expression type mismatch: cannot compare {left_domain} and {right_domain} values"
          )
        return "boolean"
      if left_domain != "numeric" or right_domain != "numeric":
        raise TypeMismatchExecutionError(
          "expression type mismatch: arithmetic requires numeric operands"
        )
      return "numeric"
    if isinstance(expression, FunctionCallExpression):
      function_name = expression.name.lower()
      if function_name not in SUPPORTED_FUNCTIONS:
        raise ExecutionError(f"unsupported function in expression: {expression.name}")
      if len(expression.arguments) != 1:
        raise ExecutionError(f"function {expression.name} expects one argument")
      argument_domain = self._infer_expression_domain(dataset, expression.arguments[0])
      if argument_domain == "null":
        raise ExecutionError(NULL_LITERAL_ERROR)
      if function_name in {"lower", "upper"}:
        if argument_domain != "string":
          raise TypeMismatchExecutionError(
            f"expression type mismatch: {function_name} requires string argument"
          )
        return "string"
      if argument_domain != "numeric":
        raise TypeMismatchExecutionError(
          f"expression type mismatch: {function_name} requires numeric argument"
        )
      return "numeric"
    raise ExecutionError("unsupported expression")

  def materialize_polars_lazy(self, path: Path | str) -> DatasetInfo:
    frame = self._collect_polars_frame("materialize", path)
    self._replace_active_with_frame(frame, command_name="materialize")
    return self.active_dataset_info(path)

  def _replace_active(self, select_sql: str, command_name: str) -> None:
    try:
      if self._active_storage == "view":
        self._connection.execute(
          f"create or replace temp table {NEXT_ACTIVE_TABLE} as {select_sql}",
        )
        self._connection.execute(f"drop view {ACTIVE_TABLE}")
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._active_storage = "table"
        self._lazy_engine = None
        self._polars_lazy_frame = None
        return
      self._connection.execute(f"create or replace temp table {NEXT_ACTIVE_TABLE} as {select_sql}")
      self._connection.execute(
        f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
      )
      self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
      self._lazy_engine = None
      self._polars_lazy_frame = None
    except duckdb.Error as exc:
      raise ExecutionError(f"{command_name} failed") from exc

  def _activate_relation(self, relation_name: str, command_name: str) -> None:
    quoted_relation = _quote_identifier(relation_name)
    try:
      self._drop_active_relation()
      self._connection.execute(
        f"create or replace temp table {ACTIVE_TABLE} as select * from {quoted_relation}"
      )
      self._active_storage = "table"
      self._lazy_engine = None
      self._polars_lazy_frame = None
    except duckdb.Error as exc:
      raise BackendExecutionError(f"{command_name} failed") from exc

  def _drop_active_relation(self) -> None:
    if self._active_storage == "view":
      self._connection.execute(f"drop view if exists {ACTIVE_TABLE}")
      return
    self._connection.execute(f"drop table if exists {ACTIVE_TABLE}")

  def _drop_load_staging_relations(self) -> None:
    self._connection.execute(f"drop table if exists {NEXT_ACTIVE_TABLE}")
    self._connection.execute(f"drop view if exists {NEXT_ACTIVE_VIEW}")

  def _bind_active_view(self) -> None:
    try:
      self._connection.execute(
        f"create or replace temp view {ACTIVE_VIEW} as select * from {ACTIVE_TABLE}"
      )
    except duckdb.Error as exc:
      raise ExecutionError("active dataset is not available") from exc

  def _fetch_table(self, sql: str, command_name: str) -> tuple[tuple[object, ...], ...]:
    try:
      return tuple(self._connection.execute(sql).fetchall())
    except duckdb.Error as exc:
      raise ExecutionError(f"{command_name} failed") from exc

  def _preview_polars_rows(
    self,
    limit: int,
    *,
    tail: bool,
  ) -> tuple[tuple[object, ...], ...]:
    if limit == 0:
      return ()
    lazy_frame = self._require_polars_lazy_frame("preview")
    try:
      frame = lazy_frame.tail(limit).collect() if tail else lazy_frame.head(limit).collect()
    except PolarsError as exc:
      command_name = "tail" if tail else "head"
      raise ExecutionError(f"{command_name} failed") from exc
    return tuple(tuple(row) for row in frame.rows())

  def _polars_row_count(self) -> int:
    lazy_frame = self._require_polars_lazy_frame("count")
    try:
      frame = lazy_frame.select(pl.len().alias("count")).collect()
    except PolarsError as exc:
      raise ExecutionError("count failed") from exc
    return int(frame.item(0, 0))

  def _collect_polars_frame(self, command_name: str, path: Path | str) -> pl.DataFrame:
    lazy_frame = self._require_polars_lazy_frame(command_name)
    try:
      return lazy_frame.collect()
    except PolarsError as exc:
      raise ExecutionError(f"{command_name} failed: {path}") from exc

  def _active_frame_for_export(self, *, command_name: str, path: Path) -> pl.DataFrame:
    if self._polars_lazy_frame is not None:
      return self._collect_polars_frame(command_name, path)
    try:
      result = self._connection.execute(f"select * from {ACTIVE_TABLE}")
      rows = result.fetchall()
      headers = tuple(column[0] for column in result.description or ())
    except duckdb.Error as exc:
      raise ExecutionError(f"{command_name} failed: {path}") from exc
    return pl.DataFrame(rows, schema=list(headers), orient="row")

  def _replace_active_with_frame(self, frame: pl.DataFrame, *, command_name: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".parquet") as temp_file:
      temp_path = Path(temp_file.name)
      try:
        frame.write_parquet(temp_path)
      except (PolarsError, OSError) as exc:
        raise ExecutionError(f"{command_name} failed") from exc
      try:
        self._connection.execute(
          f"create or replace temp table {NEXT_ACTIVE_TABLE} as select * from read_parquet(?)",
          [str(temp_path)],
        )
        self._drop_active_relation()
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
      except duckdb.Error as exc:
        raise ExecutionError(f"{command_name} failed") from exc
    self._active_storage = "table"
    self._lazy_engine = None
    self._polars_lazy_frame = None

  def _require_polars_lazy_frame(self, command_name: str) -> pl.LazyFrame:
    if self._polars_lazy_frame is None:
      raise ExecutionError(f"{command_name} failed")
    return self._polars_lazy_frame

  def _wide_j_values(self, j_variable: str) -> tuple[str, ...]:
    quoted_j = _quote_identifier(j_variable)
    sql = f"""
      select distinct cast({quoted_j} as varchar) as j_value
      from {ACTIVE_TABLE}
      where {quoted_j} is not null
      order by j_value
    """
    return tuple(str(row[0]) for row in self._fetch_table(sql, "reshape"))

  def _has_nulls(self, variable: str) -> bool:
    quoted_variable = _quote_identifier(variable)
    sql = f"select exists(select 1 from {ACTIVE_TABLE} where {quoted_variable} is null)"
    row = self._fetch_one(sql, "panel")
    return bool(row[0])

  def _has_duplicate_panel_pairs(self, metadata: PanelMetadata) -> bool:
    id_sql = _quote_identifier(metadata.id_variable)
    time_sql = _quote_identifier(metadata.time_variable)
    sql = f"""
      select exists(
        select 1
        from {ACTIVE_TABLE}
        group by {id_sql}, {time_sql}
        having count(*) > 1
      )
    """
    row = self._fetch_one(sql, "panel")
    return bool(row[0])

  def _fetch_one(self, sql: str, command_name: str) -> tuple[object, ...]:
    try:
      row = self._connection.execute(sql).fetchone()
    except duckdb.Error as exc:
      raise ExecutionError(f"{command_name} failed") from exc
    if row is None:
      raise ExecutionError(f"{command_name} failed")
    return tuple(row)

  def _rollback_transaction(self) -> None:
    try:
      self._connection.execute("rollback")
    except duckdb.Error:
      pass


def _is_numeric_type(data_type: str) -> bool:
  normalized = data_type.upper().strip()
  base = normalized.split("(", 1)[0]
  return base in NUMERIC_TYPES


def _is_unsigned_numeric_type(data_type: str) -> bool:
  normalized = data_type.upper().strip()
  base = normalized.split("(", 1)[0]
  return base in UNSIGNED_NUMERIC_TYPES


def _expression_domain_for_data_type(data_type: str) -> ExpressionDomain:
  normalized = data_type.upper()
  if _is_numeric_type(normalized):
    return "numeric"
  if normalized.startswith(("VARCHAR", "CHAR", "TEXT", "STRING")):
    return "string"
  if normalized in {"CATEGORICAL", "DICTIONARY"}:
    return "string"
  if normalized in {"BOOLEAN", "BOOL"}:
    return "boolean"
  return "other"


def _select_alias_sql(variables: tuple[str, ...]) -> str:
  return ", ".join(
    f"{_quote_identifier(variable)} as {_tabulate_alias(index)}"
    for index, variable in enumerate(variables)
  )


def _group_alias_sql(variables: tuple[str, ...]) -> str:
  return ", ".join(_tabulate_alias(index) for index, _ in enumerate(variables))


def _order_alias_sql(variables: tuple[str, ...]) -> str:
  return ", ".join(f"{_tabulate_alias(index)} nulls last" for index, _ in enumerate(variables))


def _partition_alias_sql(alias_indexes: tuple[int, ...]) -> str:
  if not alias_indexes:
    return "1"
  return ", ".join(_tabulate_alias(index) for index in alias_indexes)


def _tabulate_alias(index: int) -> str:
  return f"d{index}"


def _tabulate_predicates(
  dataset: DatasetInfo,
  dimensions: tuple[str, ...],
  *,
  condition: Expression | None,
  value_variable: str | None,
  include_missing: bool,
  compile_expression: Callable[[DatasetInfo, Expression], str],
) -> tuple[str, ...]:
  predicates: list[str] = []
  if not include_missing:
    predicates.extend(f"{_quote_identifier(variable)} is not null" for variable in dimensions)
  if value_variable is not None:
    predicates.append(f"{_quote_identifier(value_variable)} is not null")
  if condition is not None:
    predicates.append(f"({compile_expression(dataset, condition)})")
  return tuple(predicates)


def _tabulate_aggregate_sql(
  value_variable: str | None,
  statistic: Literal["count", "mean", "sum", "min", "max"] | None,
) -> str:
  if value_variable is None:
    return "count(*)"
  quoted = _quote_identifier(value_variable)
  if statistic == "count":
    return f"count({quoted})"
  if statistic == "mean":
    return f"avg(cast({quoted} as double))"
  if statistic == "sum":
    return f"sum(cast({quoted} as double))"
  if statistic == "min":
    return f"min(cast({quoted} as double))"
  if statistic == "max":
    return f"max(cast({quoted} as double))"
  raise ExecutionError("tabulate values() and stat() must be specified together")


def _tabulate_wide_result(
  long_rows: tuple[tuple[object, ...], ...],
  *,
  by_variables: tuple[str, ...],
  row_variables: tuple[str, ...],
  column_variables: tuple[str, ...],
  include_row_percent: bool,
  include_column_percent: bool,
  value_header: str,
  missing_cell_value: object,
) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
  index_width = len(by_variables) + len(row_variables)
  column_width = len(column_variables)
  column_start = index_width
  value_index = column_start + column_width
  row_percent_index = value_index + 1
  column_percent_index = row_percent_index + (1 if include_row_percent else 0)

  column_keys = tuple(
    sorted(
      _unique_tuple_values(tuple(row[column_start:value_index] for row in long_rows)),
      key=_tabulate_sort_key,
    )
  )
  index_keys = _unique_tuple_values(tuple(row[:index_width] for row in long_rows))
  cell_values = {
    _tabulate_cell_key(row[:index_width], row[column_start:value_index]): row[value_index]
    for row in long_rows
  }
  row_percent_values = (
    {
      _tabulate_cell_key(row[:index_width], row[column_start:value_index]): row[row_percent_index]
      for row in long_rows
    }
    if include_row_percent
    else {}
  )
  column_percent_values = (
    {
      _tabulate_cell_key(row[:index_width], row[column_start:value_index]): row[
        column_percent_index
      ]
      for row in long_rows
    }
    if include_column_percent
    else {}
  )

  headers = (
    by_variables
    + row_variables
    + _wide_value_headers(
      column_keys,
      value_header=value_header,
      include_row_percent=include_row_percent,
      include_column_percent=include_column_percent,
    )
  )
  rows = tuple(
    index_key
    + _wide_row_cells(
      index_key,
      column_keys,
      cell_values=cell_values,
      row_percent_values=row_percent_values,
      column_percent_values=column_percent_values,
      include_row_percent=include_row_percent,
      include_column_percent=include_column_percent,
      missing_cell_value=missing_cell_value,
    )
    for index_key in index_keys
  )
  return headers, rows


def _unique_tuple_values(rows: tuple[tuple[object, ...], ...]) -> tuple[tuple[object, ...], ...]:
  seen: set[tuple[tuple[str, object], ...]] = set()
  values: list[tuple[object, ...]] = []
  for row in rows:
    canonical_row = _canonical_tuple_key(row)
    if canonical_row in seen:
      continue
    seen.add(canonical_row)
    values.append(row)
  return tuple(values)


def _tabulate_sort_key(row: tuple[object, ...]) -> tuple[tuple[int, object], ...]:
  keys: list[tuple[int, object]] = []
  for value in row:
    if value is None:
      keys.append((2, ""))
    elif isinstance(value, bool):
      keys.append((0, int(value)))
    elif isinstance(value, (int, float, Decimal)):
      if _is_nan_value(value):
        keys.append((2, ""))
      else:
        keys.append((0, value))
    else:
      keys.append((1, str(value)))
  return tuple(keys)


def _is_nan_value(value: object) -> bool:
  return (isinstance(value, float) and math.isnan(value)) or (
    isinstance(value, Decimal) and value.is_nan()
  )


def _canonical_value_key(value: object) -> tuple[str, object]:
  if value is None:
    return ("null", "")
  if _is_nan_value(value):
    return ("nan", "")
  try:
    hash(value)
  except TypeError:
    return ("value", repr(value))
  return ("value", value)


def _canonical_tuple_key(values: tuple[object, ...]) -> tuple[tuple[str, object], ...]:
  return tuple(_canonical_value_key(value) for value in values)


def _tabulate_cell_key(
  index_key: tuple[object, ...],
  column_key: tuple[object, ...],
) -> TabulateCellKey:
  return _canonical_tuple_key(index_key), _canonical_tuple_key(column_key)


def _wide_value_headers(
  column_keys: tuple[tuple[object, ...], ...],
  *,
  value_header: str,
  include_row_percent: bool,
  include_column_percent: bool,
) -> tuple[str, ...]:
  headers: list[str] = []
  for column_key in column_keys:
    label = _column_key_label(column_key)
    headers.append(f"{label} {value_header}")
    if include_row_percent:
      headers.append(f"{label} Row %")
    if include_column_percent:
      headers.append(f"{label} Col %")
  return tuple(headers)


def _wide_row_cells(
  index_key: tuple[object, ...],
  column_keys: tuple[tuple[object, ...], ...],
  *,
  cell_values: dict[TabulateCellKey, object],
  row_percent_values: dict[TabulateCellKey, object],
  column_percent_values: dict[TabulateCellKey, object],
  include_row_percent: bool,
  include_column_percent: bool,
  missing_cell_value: object,
) -> tuple[object, ...]:
  cells: list[object] = []
  for column_key in column_keys:
    key = _tabulate_cell_key(index_key, column_key)
    cells.append(cell_values.get(key, missing_cell_value))
    if include_row_percent:
      cells.append(row_percent_values.get(key, 0.0))
    if include_column_percent:
      cells.append(column_percent_values.get(key, 0.0))
  return tuple(cells)


def _column_key_label(column_key: tuple[object, ...]) -> str:
  return " | ".join("missing" if value is None else str(value) for value in column_key)


def _linear_prediction_sql(
  *,
  predictor_names: tuple[str, ...],
  predictor_coefficients: tuple[float, ...],
  intercept: float | None,
) -> str:
  terms: list[str] = []
  if intercept is not None:
    terms.append(f"cast({_float_sql_literal(intercept)} as double)")
  for predictor, coefficient in zip(predictor_names, predictor_coefficients, strict=True):
    terms.append(
      f"cast({_float_sql_literal(coefficient)} as double) * "
      f"cast({_quote_identifier(predictor)} as double)"
    )
  if not terms:
    return "0.0"
  return " + ".join(terms)


def _cf_prediction_sql(
  *,
  first_stage_predictor_names: tuple[str, ...],
  first_stage_predictor_coefficients: tuple[float, ...],
  first_stage_intercept: float | None,
  second_stage_predictor_names: tuple[str, ...],
  second_stage_predictor_coefficients: tuple[float, ...],
  second_stage_intercept: float | None,
  second_stage_residual_index: int,
  endogenous_variable: str,
) -> str:
  first_stage_sql = _linear_prediction_sql(
    predictor_names=first_stage_predictor_names,
    predictor_coefficients=first_stage_predictor_coefficients,
    intercept=first_stage_intercept,
  )
  terms: list[str] = []
  if second_stage_intercept is not None:
    terms.append(f"cast({_float_sql_literal(second_stage_intercept)} as double)")
  for index, (predictor, coefficient) in enumerate(
    zip(
      second_stage_predictor_names,
      second_stage_predictor_coefficients,
      strict=True,
    )
  ):
    predictor_sql = (
      f"(cast({_quote_identifier(endogenous_variable)} as double) - ({first_stage_sql}))"
      if index == second_stage_residual_index
      else f"cast({_quote_identifier(predictor)} as double)"
    )
    terms.append(f"cast({_float_sql_literal(coefficient)} as double) * {predictor_sql}")
  if not terms:
    return "0.0"
  return " + ".join(terms)


def _xtdata_expression(
  variable: str,
  partition_sql: str,
  *,
  transform: Literal["within", "between"],
) -> str:
  quoted_variable = _quote_identifier(variable)
  mean_sql = f"avg(cast({quoted_variable} as double)) over (partition by {partition_sql})"
  target_name = f"{variable}_{transform}"
  if transform == "between":
    return f"{mean_sql} as {_quote_identifier(target_name)}"
  return f"(cast({quoted_variable} as double) - {mean_sql}) as {_quote_identifier(target_name)}"


def _float_sql_literal(value: float) -> str:
  if not math.isfinite(value):
    raise ExecutionError("predict failed: regression coefficient is not finite")
  return format(float(value), ".17g")


def _require_columns(
  command_name: str,
  column_types: dict[str, str],
  variables: tuple[str, ...],
) -> None:
  missing = tuple(variable for variable in variables if variable not in column_types)
  if missing:
    raise UnknownVariableError(f"{command_name} unknown variable: {', '.join(missing)}")


def _require_matching_types(
  command_name: str,
  left_types: dict[str, str],
  right_types: dict[str, str],
  variables: tuple[str, ...],
) -> None:
  for variable in variables:
    left_type = left_types[variable]
    right_type = right_types[variable]
    if left_type.upper() != right_type.upper():
      raise TypeMismatchExecutionError(
        f"{command_name} type mismatch for {variable}: {left_type} vs {right_type}"
      )


def _canonical_data_type(data_type: str) -> str:
  aliases = {
    "INT8": "TINYINT",
    "INT16": "SMALLINT",
    "INT32": "INTEGER",
    "INT64": "BIGINT",
    "UINT8": "UTINYINT",
    "UINT16": "USMALLINT",
    "UINT32": "UINTEGER",
    "UINT64": "UBIGINT",
    "FLOAT32": "FLOAT",
    "FLOAT64": "DOUBLE",
    "STRING": "VARCHAR",
  }
  normalized = data_type.upper().strip()
  return aliases.get(normalized, normalized)


def _select_list(variables: tuple[str, ...]) -> str:
  return ", ".join(_quote_identifier(variable) for variable in variables)


def _reject_existing_column(command_name: str, column_types: dict[str, str], variable: str) -> None:
  if variable in column_types:
    raise ExecutionError(f"{command_name} output column already exists: {variable}")


def _long_j_values(dataset: DatasetInfo, variables: tuple[str, ...]) -> tuple[str, ...]:
  values: list[str] = []
  seen: set[str] = set()
  for variable in variables:
    prefix = f"{variable}_"
    variable_values = tuple(
      column.name.removeprefix(prefix)
      for column in dataset.columns
      if column.name.startswith(prefix) and column.name != prefix
    )
    if not variable_values:
      raise UnknownVariableError(f"reshape long found no columns for stub: {variable}")
    for value in variable_values:
      if value not in seen:
        seen.add(value)
        values.append(value)
  return tuple(values)


def _require_long_stub_columns(
  column_types: dict[str, str],
  variable: str,
  j_values: tuple[str, ...],
) -> None:
  prefix = f"{variable}_"
  if not any(column.startswith(prefix) and column != prefix for column in column_types):
    raise UnknownVariableError(f"reshape long found no columns for stub: {variable}")
  for j_value in j_values:
    column_name = f"{variable}_{j_value}"
    if column_name not in column_types:
      raise UnknownVariableError(f"reshape long missing column: {column_name}")


def _require_wide_output_names(
  column_types: dict[str, str],
  variables: tuple[str, ...],
  identifiers: tuple[str, ...],
  j_variable: str,
  j_values: tuple[str, ...],
) -> None:
  source_columns = set(variables + identifiers + (j_variable,))
  for variable in variables:
    for j_value in j_values:
      output_name = f"{variable}_{j_value}"
      if output_name in column_types and output_name not in source_columns:
        raise ExecutionError(f"reshape wide output column already exists: {output_name}")


def _right_join_selects(
  right_dataset: DatasetInfo,
  keys: tuple[str, ...],
  left_types: dict[str, str],
  suffix: str,
) -> tuple[str, ...]:
  selects: list[str] = []
  used_output_names = set(left_types)
  for column in right_dataset.columns:
    if column.name in keys:
      continue
    base_output_name = f"{column.name}{suffix}" if column.name in used_output_names else column.name
    output_name = _unique_output_name(base_output_name, used_output_names)
    used_output_names.add(output_name)
    selects.append(
      f"right_table.{_quote_identifier(column.name)} as {_quote_identifier(output_name)}"
    )
  return tuple(selects)


def _unique_output_name(candidate: str, used_names: set[str]) -> str:
  if candidate not in used_names:
    return candidate
  counter = 2
  while f"{candidate}_{counter}" in used_names:
    counter += 1
  return f"{candidate}_{counter}"


def _quote_identifier(identifier: str) -> str:
  escaped = identifier.replace('"', '""')
  return f'"{escaped}"'


def _quote_literal(value: str) -> str:
  escaped = value.replace("'", "''")
  return f"'{escaped}'"


def _prepare_output_path(
  normalized: Path,
  original: Path,
  *,
  replace: bool,
  command_name: str,
) -> None:
  if normalized.exists() and not replace:
    raise ExecutionError(f"{command_name} target already exists: {original}")
  if normalized.exists() and not normalized.is_file():
    raise ExecutionError(f"{command_name} target is not a file: {original}")
  normalized.parent.mkdir(parents=True, exist_ok=True)


def _compile_polars_function(function_name: str, arguments: tuple[pl.Expr, ...]) -> pl.Expr:
  if function_name == "abs" and len(arguments) == 1:
    return arguments[0].abs()
  if function_name == "ceil" and len(arguments) == 1:
    return arguments[0].ceil()
  if function_name == "floor" and len(arguments) == 1:
    return arguments[0].floor()
  if function_name == "ln" and len(arguments) == 1:
    return arguments[0].log()
  if function_name == "log" and len(arguments) == 1:
    return arguments[0].log10()
  if function_name == "lower" and len(arguments) == 1:
    return arguments[0].str.to_lowercase()
  if function_name == "round" and len(arguments) == 1:
    return arguments[0].round(0)
  if function_name == "sqrt" and len(arguments) == 1:
    return arguments[0].sqrt()
  if function_name == "upper" and len(arguments) == 1:
    return arguments[0].str.to_uppercase()
  raise ExecutionError(f"unsupported function in expression: {function_name}")


def _safe_sql_numeric_result(expression_sql: str) -> str:
  return (
    "(select case when isfinite(cast(__tabdat_numeric_value as double)) "
    "then __tabdat_numeric_value else NULL end "
    f"from (select try({expression_sql}) as __tabdat_numeric_value) "
    "as __tabdat_numeric_result)"
  )


def _is_numeric_result_expression(expression: Expression) -> bool:
  if isinstance(expression, UnaryExpression):
    return True
  if isinstance(expression, BinaryExpression):
    return expression.operator in {"+", "-", "*", "/"}
  if isinstance(expression, FunctionCallExpression):
    return expression.name.lower() in NUMERIC_FUNCTIONS
  return False


def _normalize_polars_numeric_result(expression: pl.Expr) -> pl.Expr:
  finite_value = expression.cast(pl.Float64)
  # Keep the cast in the finite probe; Polars can otherwise move it after is_finite when the
  # result branch reuses the same expression, which is unsupported for Decimal inputs.
  finite_probe = (finite_value + pl.lit(0.0)).is_finite()
  return pl.when(finite_probe).then(finite_value).otherwise(pl.lit(None))


def _contains_null_literal(expression: Expression) -> bool:
  if isinstance(expression, NullExpression):
    return True
  if isinstance(expression, (IdentifierExpression, NumberExpression, StringExpression)):
    return False
  if isinstance(expression, UnaryExpression):
    return _contains_null_literal(expression.operand)
  if isinstance(expression, BinaryExpression):
    return _contains_null_literal(expression.left) or _contains_null_literal(expression.right)
  if isinstance(expression, FunctionCallExpression):
    return any(_contains_null_literal(argument) for argument in expression.arguments)
  return False


def _contains_unsigned_identifier(
  column_types: dict[str, str],
  expression: Expression,
) -> bool:
  if isinstance(expression, IdentifierExpression):
    data_type = column_types.get(expression.name)
    return data_type is not None and _is_unsigned_numeric_type(data_type)
  if isinstance(expression, (NumberExpression, StringExpression, NullExpression)):
    return False
  if isinstance(expression, UnaryExpression):
    return _contains_unsigned_identifier(column_types, expression.operand)
  if isinstance(expression, BinaryExpression):
    return _contains_unsigned_identifier(
      column_types, expression.left
    ) or _contains_unsigned_identifier(column_types, expression.right)
  if isinstance(expression, FunctionCallExpression):
    return any(
      _contains_unsigned_identifier(column_types, argument) for argument in expression.arguments
    )
  return False


def _has_unsafe_unsigned_arithmetic(
  column_types: dict[str, str],
  expression: Expression,
) -> bool:
  if isinstance(expression, UnaryExpression):
    return _contains_unsigned_identifier(column_types, expression.operand)
  if isinstance(expression, BinaryExpression):
    if expression.operator == "-" and (
      _contains_unsigned_identifier(column_types, expression.left)
      or _contains_unsigned_identifier(column_types, expression.right)
    ):
      return True
    return _has_unsafe_unsigned_arithmetic(
      column_types,
      expression.left,
    ) or _has_unsafe_unsigned_arithmetic(column_types, expression.right)
  if isinstance(expression, FunctionCallExpression):
    return any(
      _has_unsafe_unsigned_arithmetic(column_types, argument) for argument in expression.arguments
    )
  return False


def _contains_negative_numeric_literal(expression: Expression) -> bool:
  if isinstance(expression, NumberExpression):
    return expression.value < 0
  if isinstance(expression, UnaryExpression) and isinstance(expression.operand, NumberExpression):
    return expression.operand.value != 0
  return False


def _has_unsafe_unsigned_numeric_pair(
  column_types: dict[str, str],
  expression: BinaryExpression,
) -> bool:
  return (
    _contains_unsigned_identifier(column_types, expression.left)
    and _contains_negative_numeric_literal(expression.right)
  ) or (
    _contains_unsigned_identifier(column_types, expression.right)
    and _contains_negative_numeric_literal(expression.left)
  )


def _null_cast_type(data_type: str) -> str:
  normalized = data_type.upper().strip()
  arrow_types = {
    "INT8": "TINYINT",
    "INT16": "SMALLINT",
    "INT32": "INTEGER",
    "INT64": "BIGINT",
    "UINT8": "UTINYINT",
    "UINT16": "USMALLINT",
    "UINT32": "UINTEGER",
    "UINT64": "UBIGINT",
    "FLOAT32": "FLOAT",
    "FLOAT64": "DOUBLE",
    "STRING": "VARCHAR",
    "CATEGORICAL": "VARCHAR",
    "BOOL": "BOOLEAN",
  }
  return arrow_types.get(normalized, data_type)


def _polars_dtype_name(dtype: pl.DataType) -> str:
  return str(dtype).upper()


def resolve_parquet_source(path: Path | str) -> LoadSource:
  return resolve_load_source(path)


def _nullable_float(value: float | None) -> float | None:
  if value is None:
    return None
  return float(value)


def resolve_load_source(path: Path | str) -> LoadSource:
  if isinstance(path, str) and "://" in path:
    parsed = urlparse(path)
    suffix = parsed.path.lower()
    fmt_items: list[tuple[str, DataFormat]] = [
      (".parquet", "parquet"),
      (".dta", "stata"),
      (".csv", "csv"),
      (".feather", "feather"),
      (".arrow", "arrow"),
    ]
    for ext, fmt in fmt_items:
      if suffix.endswith(ext):
        if not remote_scheme_supported(fmt, parsed.scheme):
          if fmt == "parquet":
            raise ExecutionError("use remote Parquet supports http, https, and s3 URLs")
          elif fmt == "stata":
            raise ExecutionError("use remote Stata files support http and https URLs")
          else:
            schemes = list(ingestion_adapter_for(fmt).supported_remote_schemes)
            if len(schemes) == 2:
              schemes_str = f"{schemes[0]} and {schemes[1]}"
            elif len(schemes) > 2:
              schemes_str = ", ".join(schemes[:-1]) + ", and " + schemes[-1]
            else:
              schemes_str = schemes[0]
            fmt_cap = fmt.capitalize()
            raise ExecutionError(f"use remote {fmt_cap} files support {schemes_str} URLs")
        return LoadSource(format=fmt, read_path=path, display_path=path, is_remote=True)
    raise ExecutionError("use only supports .parquet, .dta, .csv, .feather, and .arrow files")

  normalized = Path(path).expanduser()
  suffix = normalized.suffix.lower()
  format_map: dict[str, DataFormat] = {
    ".parquet": "parquet",
    ".dta": "stata",
    ".csv": "csv",
    ".feather": "feather",
    ".arrow": "arrow",
  }
  if suffix not in format_map:
    raise ExecutionError("use only supports .parquet, .dta, .csv, .feather, and .arrow files")
  if not normalized.exists():
    raise ExecutionError(f"use could not find file: {path}")
  if not normalized.is_file():
    raise ExecutionError(f"use expected a file path: {path}")
  fmt = format_map[suffix]
  return LoadSource(
    format=fmt,
    read_path=str(normalized),
    display_path=normalized,
    is_remote=False,
  )


def _require_result_query(query: str) -> None:
  first_word = query.lstrip().split(maxsplit=1)[0].lower() if query.strip() else ""
  if first_word not in {"select", "with"}:
    raise ExecutionError("sql only supports select or with queries in Phase 4")


def _validate_user_table_name(table_name: str) -> None:
  if not table_name.isidentifier():
    raise ReservedNameError(f"invalid table name: {table_name}")
  normalized = table_name.lower()
  if normalized == "active" or normalized.startswith("__tabdat_"):
    raise ReservedNameError(f"reserved table name: {table_name}")


def _named_table_identifier(table_name: str) -> str:
  return f"__tabdat_named_{table_name}"

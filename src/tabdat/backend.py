"""DuckDB-backed dataset operations."""

from pathlib import Path
from typing import Literal

import duckdb

from tabdat.errors import ExecutionError
from tabdat.models import (
  BinaryExpression,
  CodebookRow,
  ColumnInfo,
  DatasetInfo,
  Expression,
  FunctionCallExpression,
  IdentifierExpression,
  NumberExpression,
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
  "FLOAT",
  "DOUBLE",
  "DECIMAL",
)
SUPPORTED_FUNCTIONS = {"abs", "ceil", "floor", "ln", "log", "lower", "round", "sqrt", "upper"}
ACTIVE_TABLE = "__tabdat_active"
ACTIVE_VIEW = "active"


class DuckDBBackend:
  """Small DuckDB adapter for the active Phase 3 dataset."""

  def __init__(self) -> None:
    self._connection = duckdb.connect(database=":memory:")
    self._active_storage: Literal["table", "view"] = "table"
    self._lazy_engine: Literal["duckdb", "polars"] | None = None

  def close(self) -> None:
    self._connection.close()

  def inspect_parquet(
    self,
    path: Path,
    *,
    execution_mode: Literal["eager", "lazy"] = "eager",
    lazy_engine: Literal["duckdb", "polars"] | None = None,
  ) -> DatasetInfo:
    normalized = path.expanduser()
    if normalized.suffix.lower() != ".parquet":
      raise ExecutionError("use only supports local .parquet files in Phase 1")
    if not normalized.exists():
      raise ExecutionError(f"use could not find file: {path}")
    if not normalized.is_file():
      raise ExecutionError(f"use expected a file path: {path}")

    self._lazy_engine = lazy_engine if execution_mode == "lazy" else None
    self._active_storage = "view" if execution_mode == "lazy" else "table"

    try:
      if execution_mode == "lazy":
        self._connection.execute(f"drop table if exists {ACTIVE_TABLE}")
        self._connection.execute(
          f"""
          create or replace temp view {ACTIVE_TABLE}
          as select * from read_parquet({_quote_literal(str(normalized))})
          """,
        )
      else:
        self._connection.execute(f"drop view if exists {ACTIVE_TABLE}")
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from read_parquet(?)",
          [str(normalized)],
        )
    except duckdb.Error as exc:
      raise ExecutionError(f"use could not read Parquet file: {path}") from exc

    return self.active_dataset_info(normalized)

  def active_dataset_info(self, path: Path) -> DatasetInfo:
    try:
      description = self._connection.execute(f"describe {ACTIVE_TABLE}").fetchall()
      row_count_row = self._connection.execute(f"select count(*) from {ACTIVE_TABLE}").fetchone()
    except duckdb.Error as exc:
      raise ExecutionError("active dataset is not available") from exc
    if row_count_row is None:
      raise ExecutionError("active dataset is not available")
    row_count = row_count_row[0]
    columns = tuple(ColumnInfo(name=row[0], data_type=row[1]) for row in description)
    return DatasetInfo(
      path=path,
      row_count=row_count,
      columns=columns,
      execution_mode="lazy" if self._active_storage == "view" else "eager",
      lazy_engine=self._lazy_engine,
    )

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
      raise ExecutionError(f"summarize requires numeric variables: {', '.join(non_numeric)}")

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
      raise ExecutionError(f"summarize requires numeric variables: {', '.join(non_numeric)}")

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
    if limit == 0:
      return ()

    query = (
      f"""
        select * exclude (__tabdat_row_number)
        from (
          select
            row_number() over () as __tabdat_row_number,
            *
          from {ACTIVE_TABLE}
        )
        order by __tabdat_row_number desc
        limit ?
      """
      if tail
      else f"select * from {ACTIVE_TABLE} limit ?"
    )
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
    condition_sql = self._compile_expression(dataset, condition)
    predicate = condition_sql if keep else f"not ({condition_sql})"
    command_name = "keep" if keep else "drop"
    self._replace_active(
      f"select * from {ACTIVE_TABLE} where {predicate}",
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
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("replace", column_types, (variable,))
    expression_sql = self._compile_expression(dataset, expression)
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

  def tabulate(
    self,
    dataset: DatasetInfo,
    variables: tuple[str, ...],
    *,
    row_percent: bool,
    column_percent: bool,
    include_missing: bool,
  ) -> tuple[tuple[object, ...], ...]:
    column_types = {column.name: column.data_type for column in dataset.columns}
    _require_columns("tabulate", column_types, variables)
    if len(variables) == 1:
      return self._tabulate_one_way(variables[0], include_missing=include_missing)
    return self._tabulate_two_way(
      variables[0],
      variables[1],
      row_percent=row_percent,
      column_percent=column_percent,
      include_missing=include_missing,
    )

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
        raise ExecutionError(
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
        raise ExecutionError(f"plot requires numeric variables: {', '.join(non_numeric)}")
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
      order by count desc, value
      """,
      "bar",
    )

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

  def _tabulate_one_way(
    self,
    variable: str,
    *,
    include_missing: bool,
  ) -> tuple[tuple[object, ...], ...]:
    quoted = _quote_identifier(variable)
    where_sql = "" if include_missing else f"where {quoted} is not null"
    sql = f"""
      select
        {quoted} as value,
        count(*) as count,
        100.0 * count(*) / sum(count(*)) over () as percent
      from {ACTIVE_TABLE}
      {where_sql}
      group by {quoted}
      order by {quoted}
    """
    return self._fetch_table(sql, "tabulate")

  def _tabulate_two_way(
    self,
    first: str,
    second: str,
    *,
    row_percent: bool,
    column_percent: bool,
    include_missing: bool,
  ) -> tuple[tuple[object, ...], ...]:
    first_sql = _quote_identifier(first)
    second_sql = _quote_identifier(second)
    predicates = (
      () if include_missing else (f"{first_sql} is not null", f"{second_sql} is not null")
    )
    where_sql = "" if not predicates else f"where {' and '.join(predicates)}"
    extra_columns: list[str] = []
    if row_percent:
      extra_columns.append(
        "100.0 * count / sum(count) over (partition by first_value) as row_percent"
      )
    if column_percent:
      extra_columns.append(
        "100.0 * count / sum(count) over (partition by second_value) as column_percent"
      )
    extra_sql = "" if not extra_columns else ", " + ", ".join(extra_columns)
    sql = f"""
      with counts as (
        select
          {first_sql} as first_value,
          {second_sql} as second_value,
          count(*) as count
        from {ACTIVE_TABLE}
        {where_sql}
        group by {first_sql}, {second_sql}
      )
      select first_value, second_value, count{extra_sql}
      from counts
      order by first_value, second_value
    """
    return self._fetch_table(sql, "tabulate")

  def _compile_expression(self, dataset: DatasetInfo, expression: Expression) -> str:
    column_types = {column.name: column.data_type for column in dataset.columns}
    if isinstance(expression, IdentifierExpression):
      _require_columns("expression", column_types, (expression.name,))
      return _quote_identifier(expression.name)
    if isinstance(expression, NumberExpression):
      return str(expression.value)
    if isinstance(expression, StringExpression):
      return _quote_literal(expression.value)
    if isinstance(expression, UnaryExpression):
      return f"-({self._compile_expression(dataset, expression.operand)})"
    if isinstance(expression, BinaryExpression):
      left = self._compile_expression(dataset, expression.left)
      right = self._compile_expression(dataset, expression.right)
      return f"({left} {expression.operator} {right})"
    if isinstance(expression, FunctionCallExpression):
      function_name = expression.name.lower()
      if function_name not in SUPPORTED_FUNCTIONS:
        raise ExecutionError(f"unsupported function in expression: {expression.name}")
      arguments = ", ".join(
        self._compile_expression(dataset, argument) for argument in expression.arguments
      )
      return f"{function_name}({arguments})"
    raise ExecutionError("unsupported expression")

  def _replace_active(self, select_sql: str, command_name: str) -> None:
    try:
      if self._active_storage == "view":
        self._connection.execute(
          f"create or replace temp table __tabdat_next as {select_sql}",
        )
        self._connection.execute(f"drop view {ACTIVE_TABLE}")
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from __tabdat_next"
        )
        self._connection.execute("drop table __tabdat_next")
        self._active_storage = "table"
        return
      self._connection.execute(f"create or replace temp table __tabdat_next as {select_sql}")
      self._connection.execute(
        f"create or replace temp table {ACTIVE_TABLE} as select * from __tabdat_next"
      )
      self._connection.execute("drop table __tabdat_next")
    except duckdb.Error as exc:
      raise ExecutionError(f"{command_name} failed") from exc

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


def _is_numeric_type(data_type: str) -> bool:
  normalized = data_type.upper()
  return normalized.startswith(NUMERIC_TYPES)


def _require_columns(
  command_name: str,
  column_types: dict[str, str],
  variables: tuple[str, ...],
) -> None:
  missing = tuple(variable for variable in variables if variable not in column_types)
  if missing:
    raise ExecutionError(f"{command_name} unknown variable: {', '.join(missing)}")


def _select_list(variables: tuple[str, ...]) -> str:
  return ", ".join(_quote_identifier(variable) for variable in variables)


def _quote_identifier(identifier: str) -> str:
  escaped = identifier.replace('"', '""')
  return f'"{escaped}"'


def _quote_literal(value: str) -> str:
  escaped = value.replace("'", "''")
  return f"'{escaped}'"


def _require_result_query(query: str) -> None:
  first_word = query.lstrip().split(maxsplit=1)[0].lower() if query.strip() else ""
  if first_word not in {"select", "with"}:
    raise ExecutionError("sql only supports select or with queries in Phase 4")

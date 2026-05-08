"""DuckDB-backed dataset operations."""

from pathlib import Path
from typing import Literal, cast

import duckdb

from tabdat.errors import (
  BackendExecutionError,
  ExecutionError,
  ReservedNameError,
  TypeMismatchExecutionError,
  UnknownVariableError,
)
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
NEXT_ACTIVE_TABLE = "__tabdat_next"
NEXT_ACTIVE_VIEW = "__tabdat_next_view"


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

    try:
      if execution_mode == "lazy":
        read_sql = f"select * from read_parquet({_quote_literal(str(normalized))})"
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
          [str(normalized)],
        )
        self._drop_active_relation()
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._lazy_engine = None
        self._active_storage = "table"
    except duckdb.Error as exc:
      self._drop_load_staging_relations()
      raise ExecutionError(f"use could not read Parquet file: {path}") from exc

    return self.active_dataset_info(normalized)

  def active_dataset_info(self, path: Path) -> DatasetInfo:
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
    internal_name = _named_table_identifier(table_name)
    self._activate_relation(internal_name, "use")
    return self.active_dataset_info(Path(table_name))

  def store_active_as_named_table(self, table_name: str) -> DatasetInfo:
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
      {how} join {_quote_identifier(internal_name)} as right_table
        on {predicates}
      order by left_table.__tabdat_join_order
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
    _validate_user_table_name(table_name)
    left_types = {column.name: column.data_type for column in dataset.columns}
    right_types = {column.name: column.data_type for column in append_dataset.columns}
    _require_columns("append", left_types, tuple(right_types))
    missing_right = tuple(
      column.name for column in dataset.columns if column.name not in right_types
    )
    if missing_right:
      raise UnknownVariableError(
        f"append unknown variable in {table_name}: {', '.join(missing_right)}"
      )
    _require_matching_types("append", left_types, right_types, tuple(left_types))

    internal_name = _named_table_identifier(table_name)
    select_sql = _select_list(tuple(column.name for column in dataset.columns))
    self._replace_active(
      f"""
      select {select_sql}
      from {ACTIVE_TABLE}
      union all
      select {select_sql}
      from {_quote_identifier(internal_name)}
      """,
      "append",
    )
    return self.active_dataset_info(dataset.path)

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

  def save_active_parquet(self, path: Path, *, replace: bool) -> None:
    normalized = path.expanduser()
    if normalized.suffix.lower() != ".parquet":
      raise ExecutionError("save only supports .parquet files in Phase 9")
    if normalized.exists() and not replace:
      raise ExecutionError(f"save target already exists: {path}")
    if normalized.exists() and not normalized.is_file():
      raise ExecutionError(f"save target is not a file: {path}")
    normalized.parent.mkdir(parents=True, exist_ok=True)
    try:
      self._connection.execute(
        f"copy (select * from {ACTIVE_TABLE}) to ? (format parquet)",
        [str(normalized)],
      )
    except duckdb.Error as exc:
      raise ExecutionError(f"save failed: {path}") from exc

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
          f"create or replace temp table {NEXT_ACTIVE_TABLE} as {select_sql}",
        )
        self._connection.execute(f"drop view {ACTIVE_TABLE}")
        self._connection.execute(
          f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
        )
        self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
        self._active_storage = "table"
        return
      self._connection.execute(f"create or replace temp table {NEXT_ACTIVE_TABLE} as {select_sql}")
      self._connection.execute(
        f"create or replace temp table {ACTIVE_TABLE} as select * from {NEXT_ACTIVE_TABLE}"
      )
      self._connection.execute(f"drop table {NEXT_ACTIVE_TABLE}")
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

  def _wide_j_values(self, j_variable: str) -> tuple[str, ...]:
    quoted_j = _quote_identifier(j_variable)
    sql = f"""
      select distinct cast({quoted_j} as varchar) as j_value
      from {ACTIVE_TABLE}
      where {quoted_j} is not null
      order by j_value
    """
    return tuple(str(row[0]) for row in self._fetch_table(sql, "reshape"))


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


def _select_list(variables: tuple[str, ...]) -> str:
  return ", ".join(_quote_identifier(variable) for variable in variables)


def _reject_existing_column(command_name: str, column_types: dict[str, str], variable: str) -> None:
  if variable in column_types:
    raise ExecutionError(f"{command_name} output column already exists: {variable}")


def _long_j_values(dataset: DatasetInfo, variables: tuple[str, ...]) -> tuple[str, ...]:
  first_stub = variables[0]
  prefix = f"{first_stub}_"
  values = tuple(
    column.name.removeprefix(prefix)
    for column in dataset.columns
    if column.name.startswith(prefix) and column.name != prefix
  )
  if not values:
    raise UnknownVariableError(f"reshape long found no columns for stub: {first_stub}")
  return values


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

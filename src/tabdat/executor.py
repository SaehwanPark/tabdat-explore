"""Command executor and session state."""

from dataclasses import dataclass, field
from pathlib import Path

from tabdat.backend import DuckDBBackend
from tabdat.config import TabDatConfig, set_config_value
from tabdat.errors import ExecutionError, NoActiveDatasetError, UnknownTableError
from tabdat.models import (
  ActivateResult,
  BarCommand,
  ByCommand,
  CodebookCommand,
  CodebookResult,
  CollapseCommand,
  Command,
  CountCommand,
  CountResult,
  DatasetInfo,
  DescribeCommand,
  DescribeResult,
  DropCommand,
  ExitCommand,
  ExportCommand,
  GenerateCommand,
  HeadCommand,
  HistogramCommand,
  KeepCommand,
  LoadResult,
  PlotResult,
  PreviewResult,
  RenameCommand,
  ReplaceCommand,
  Result,
  SaveCommand,
  SaveResult,
  ScatterCommand,
  SelectCommand,
  SetCommand,
  SetResult,
  SqlCommand,
  SqlCreateResult,
  SummarizeCommand,
  SummarizeResult,
  TableResult,
  TabulateCommand,
  TailCommand,
  TransformResult,
  UseCommand,
)
from tabdat.visualization import default_plot_path, save_bar, save_histogram, save_scatter


@dataclass
class SessionState:
  active_dataset: DatasetInfo | None = None
  active_table_name: str | None = None
  tables: dict[str, DatasetInfo] = field(default_factory=dict)
  config: TabDatConfig = TabDatConfig()


class Executor:
  def __init__(
    self,
    backend: DuckDBBackend | None = None,
    *,
    config: TabDatConfig | None = None,
  ) -> None:
    self.backend = backend or DuckDBBackend()
    self.state = SessionState(config=config or TabDatConfig())

  def close(self) -> None:
    self.backend.close()

  def execute(self, command: Command) -> Result | None:
    if isinstance(command, UseCommand):
      return self._execute_use(command)

    if isinstance(command, DescribeCommand):
      dataset = self._require_active_dataset("describe")
      return DescribeResult(dataset=dataset)

    if isinstance(command, SummarizeCommand):
      dataset = self._require_active_dataset("summarize")
      summary_rows = self.backend.summarize(dataset, command.variables)
      return SummarizeResult(rows=summary_rows)

    if isinstance(command, CodebookCommand):
      dataset = self._require_active_dataset("codebook")
      codebook_rows = self.backend.codebook(dataset, command.variables)
      return CodebookResult(rows=codebook_rows)

    if isinstance(command, CountCommand):
      self._require_active_dataset("count")
      return CountResult(row_count=self.backend.active_row_count())

    if isinstance(command, HeadCommand):
      dataset = self._require_active_dataset("head")
      preview_rows = self.backend.preview_rows(command.limit)
      return PreviewResult(
        columns=tuple(column.name for column in dataset.columns),
        rows=preview_rows,
      )

    if isinstance(command, TailCommand):
      dataset = self._require_active_dataset("tail")
      preview_rows = self.backend.preview_rows(command.limit, tail=True)
      return PreviewResult(
        columns=tuple(column.name for column in dataset.columns),
        rows=preview_rows,
      )

    if isinstance(command, KeepCommand):
      return self._execute_keep(command)

    if isinstance(command, DropCommand):
      return self._execute_drop(command)

    if isinstance(command, SelectCommand):
      return self._execute_select(command)

    if isinstance(command, RenameCommand):
      return self._execute_rename(command)

    if isinstance(command, GenerateCommand):
      return self._execute_generate(command)

    if isinstance(command, ReplaceCommand):
      return self._execute_replace(command)

    if isinstance(command, TabulateCommand):
      dataset = self._require_active_dataset("tabulate")
      table_rows = self.backend.tabulate(
        dataset,
        command.variables,
        row_percent=command.row_percent,
        column_percent=command.column_percent,
        include_missing=command.include_missing,
      )
      headers: tuple[str, ...] = _tabulate_headers(command)
      return TableResult(headers=headers, rows=table_rows)

    if isinstance(command, CollapseCommand):
      return self._execute_collapse(command)

    if isinstance(command, SqlCommand):
      return self._execute_sql(command)

    if isinstance(command, HistogramCommand):
      dataset = self._require_active_dataset("histogram")
      rows = self.backend.plot_rows(dataset, (command.variable,), numeric=True)
      path = command.saving or self._default_plot_path("histogram", (command.variable,))
      saved_path = save_histogram(rows, command.variable, path, bins=command.bins)
      return PlotResult(path=saved_path, should_open=command.open_artifact)

    if isinstance(command, ScatterCommand):
      dataset = self._require_active_dataset("scatter")
      rows = self.backend.plot_rows(
        dataset,
        (command.y_variable, command.x_variable),
        numeric=True,
      )
      path = command.saving or default_plot_path(
        "scatter",
        (command.y_variable, command.x_variable),
        artifact_dir=self.state.config.artifact_dir,
        graph_format=self.state.config.graph_format,
      )
      saved_path = save_scatter(rows, command.y_variable, command.x_variable, path)
      return PlotResult(path=saved_path, should_open=command.open_artifact)

    if isinstance(command, BarCommand):
      dataset = self._require_active_dataset("bar")
      rows = self.backend.bar_counts(
        dataset,
        command.variable,
        include_missing=command.include_missing,
      )
      path = command.saving or self._default_plot_path("bar", (command.variable,))
      saved_path = save_bar(rows, command.variable, path)
      return PlotResult(path=saved_path, should_open=command.open_artifact)

    if isinstance(command, ByCommand):
      return self._execute_by(command)

    if isinstance(command, ExitCommand):
      return None

    if isinstance(command, SetCommand):
      self.state.config = set_config_value(self.state.config, command.name, command.value)
      return SetResult(command.name, _setting_display_value(command.name, self.state.config))

    if isinstance(command, SaveCommand | ExportCommand):
      dataset = self._require_active_dataset("save")
      self.backend.save_active_parquet(command.path, replace=command.replace)
      saved_dataset = DatasetInfo(
        path=command.path,
        row_count=self.backend.active_row_count(),
        columns=dataset.columns,
        execution_mode="eager",
        lazy_engine=None,
      )
      return SaveResult(command.path, saved_dataset)

    raise ExecutionError("unsupported command")

  def _default_plot_path(self, command_name: str, variables: tuple[str, ...]) -> Path:
    return default_plot_path(
      command_name,
      variables,
      artifact_dir=self.state.config.artifact_dir,
      graph_format=self.state.config.graph_format,
    )

  def _execute_use(self, command: UseCommand) -> LoadResult | ActivateResult:
    if self._should_activate_named_table(command):
      table_name = command.path.as_posix()
      dataset = self.state.tables.get(table_name)
      if dataset is None:
        raise UnknownTableError(f"unknown table: {table_name}")
      activated = self.backend.activate_named_table(table_name)
      self._set_active_dataset(activated, active_table_name=table_name)
      return ActivateResult(table_name=table_name, dataset=activated)

    dataset = self.backend.inspect_parquet(
      command.path,
      execution_mode=command.execution_mode,
      lazy_engine=command.lazy_engine,
    )
    self.state.active_table_name = None
    self._set_active_dataset(dataset, active_table_name=None)
    return LoadResult(dataset=dataset)

  def _execute_keep(self, command: KeepCommand) -> TransformResult:
    dataset = self._require_active_dataset("keep")
    if command.condition is not None:
      next_dataset = self.backend.filter_rows(dataset, command.condition, keep=True)
      return self._record_transform("Kept matching rows", next_dataset)
    next_dataset = self.backend.keep_columns(dataset, command.variables)
    return self._record_transform("Kept selected columns", next_dataset)

  def _execute_drop(self, command: DropCommand) -> TransformResult:
    dataset = self._require_active_dataset("drop")
    if command.condition is not None:
      next_dataset = self.backend.filter_rows(dataset, command.condition, keep=False)
      return self._record_transform("Dropped matching rows", next_dataset)
    next_dataset = self.backend.drop_columns(dataset, command.variables)
    return self._record_transform("Dropped selected columns", next_dataset)

  def _execute_select(self, command: SelectCommand) -> TransformResult:
    dataset = self._require_active_dataset("select")
    next_dataset = self.backend.keep_columns(dataset, command.variables)
    return self._record_transform("Selected columns", next_dataset)

  def _execute_rename(self, command: RenameCommand) -> TransformResult:
    dataset = self._require_active_dataset("rename")
    next_dataset = self.backend.rename_column(dataset, command.old_name, command.new_name)
    return self._record_transform(f"Renamed {command.old_name} to {command.new_name}", next_dataset)

  def _execute_generate(self, command: GenerateCommand) -> TransformResult:
    dataset = self._require_active_dataset("generate")
    next_dataset = self.backend.generate_column(dataset, command.variable, command.expression)
    return self._record_transform(f"Generated {command.variable}", next_dataset)

  def _execute_replace(self, command: ReplaceCommand) -> TransformResult:
    dataset = self._require_active_dataset("replace")
    next_dataset = self.backend.replace_column(
      dataset,
      command.variable,
      command.expression,
      command.condition,
    )
    return self._record_transform(f"Replaced {command.variable}", next_dataset)

  def _execute_collapse(self, command: CollapseCommand) -> TransformResult:
    dataset = self._require_active_dataset("collapse")
    next_dataset = self.backend.collapse(
      dataset,
      command.statistic,
      command.variables,
      command.groups,
    )
    return self._record_transform("Collapsed dataset", next_dataset)

  def _execute_sql(self, command: SqlCommand) -> SqlCreateResult | TableResult:
    dataset = self._require_active_dataset("sql")
    if command.into is not None:
      next_dataset = self.backend.create_named_table_from_sql(
        dataset,
        command.query,
        command.into,
      )
      self._set_active_dataset(next_dataset, active_table_name=command.into)
      return SqlCreateResult(command.into, next_dataset)
    sql_headers, sql_rows = self.backend.run_sql(command.query)
    return TableResult(headers=sql_headers, rows=sql_rows)

  def _record_transform(self, message: str, dataset: DatasetInfo) -> TransformResult:
    self._set_active_dataset(dataset)
    return TransformResult(message, dataset)

  def _require_active_dataset(self, command_name: str) -> DatasetInfo:
    if self.state.active_dataset is None:
      raise NoActiveDatasetError(f"{command_name} requires an active dataset; run use <path> first")
    return self.state.active_dataset

  def _set_active_dataset(
    self,
    dataset: DatasetInfo,
    *,
    active_table_name: str | None = None,
  ) -> None:
    self.state.active_dataset = dataset
    if active_table_name is not None:
      self.state.active_table_name = active_table_name
      self.state.tables[active_table_name] = dataset
      return
    if self.state.active_table_name is not None:
      updated = self.backend.store_active_as_named_table(self.state.active_table_name)
      self.state.active_dataset = updated
      self.state.tables[self.state.active_table_name] = updated
      return
    self.state.active_table_name = None

  def _should_activate_named_table(self, command: UseCommand) -> bool:
    table_name = command.path.as_posix()
    if table_name in self.state.tables:
      if command.execution_mode != "eager" or command.lazy_engine is not None:
        raise ExecutionError("use options are not supported for named table activation")
      return True
    if command.execution_mode != "eager" or command.lazy_engine is not None:
      return False
    if command.path.exists():
      return False
    if command.path.suffix:
      return False
    if "/" in table_name:
      return False
    raise UnknownTableError(f"unknown table: {table_name}")

  def _execute_by(self, command: ByCommand) -> TableResult:
    dataset = self._require_active_dataset("by")
    if isinstance(command.command, SummarizeCommand):
      table_rows = self.backend.grouped_summarize(
        dataset,
        command.groups,
        command.command.variables,
      )
      variables = command.command.variables or _default_grouped_summary_variables(
        dataset,
        command.groups,
      )
      summary_headers: tuple[str, ...] = command.groups + tuple(
        f"mean_{variable}" for variable in variables
      )
      return TableResult(headers=summary_headers, rows=table_rows)
    if isinstance(command.command, CountCommand):
      table_rows = self.backend.grouped_count(dataset, command.groups)
      count_headers: tuple[str, ...] = command.groups + ("Count",)
      return TableResult(headers=count_headers, rows=table_rows)
    raise ExecutionError("by only supports summarize and count in Phase 3")


def _tabulate_headers(command: TabulateCommand) -> tuple[str, ...]:
  if len(command.variables) == 1:
    return (command.variables[0], "Count", "Percent")
  headers: tuple[str, ...] = (command.variables[0], command.variables[1], "Count")
  if command.row_percent:
    headers += ("Row %",)
  if command.column_percent:
    headers += ("Col %",)
  return headers


def _default_grouped_summary_variables(
  dataset: DatasetInfo,
  groups: tuple[str, ...],
) -> tuple[str, ...]:
  return tuple(
    column.name
    for column in dataset.columns
    if column.name not in groups and _is_numeric_type(column.data_type)
  )


def _is_numeric_type(data_type: str) -> bool:
  normalized = data_type.upper()
  numeric_prefixes = (
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
  return normalized.startswith(numeric_prefixes)


def _setting_display_value(name: str, config: TabDatConfig) -> str:
  if name == "graph_format":
    return config.graph_format
  if name == "artifact_dir":
    return str(config.artifact_dir)
  if name == "graph_open":
    return "on" if config.graph_open else "off"
  raise ExecutionError(f"unknown setting: {name}")

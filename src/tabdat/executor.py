"""Command executor and session state."""

from dataclasses import dataclass

from tabdat.backend import DuckDBBackend
from tabdat.errors import ExecutionError
from tabdat.models import (
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
  ScatterCommand,
  SelectCommand,
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


class Executor:
  def __init__(self, backend: DuckDBBackend | None = None) -> None:
    self.backend = backend or DuckDBBackend()
    self.state = SessionState()

  def close(self) -> None:
    self.backend.close()

  def execute(self, command: Command) -> Result | None:
    if isinstance(command, UseCommand):
      dataset = self.backend.inspect_parquet(command.path)
      self.state.active_dataset = dataset
      return LoadResult(dataset=dataset)

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
      dataset = self._require_active_dataset("count")
      return CountResult(row_count=dataset.row_count)

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
      dataset = self._require_active_dataset("keep")
      if command.condition is not None:
        next_dataset = self.backend.filter_rows(dataset, command.condition, keep=True)
        self.state.active_dataset = next_dataset
        return TransformResult("Kept matching rows", next_dataset)
      next_dataset = self.backend.keep_columns(dataset, command.variables)
      self.state.active_dataset = next_dataset
      return TransformResult("Kept selected columns", next_dataset)

    if isinstance(command, DropCommand):
      dataset = self._require_active_dataset("drop")
      if command.condition is not None:
        next_dataset = self.backend.filter_rows(dataset, command.condition, keep=False)
        self.state.active_dataset = next_dataset
        return TransformResult("Dropped matching rows", next_dataset)
      next_dataset = self.backend.drop_columns(dataset, command.variables)
      self.state.active_dataset = next_dataset
      return TransformResult("Dropped selected columns", next_dataset)

    if isinstance(command, SelectCommand):
      dataset = self._require_active_dataset("select")
      next_dataset = self.backend.keep_columns(dataset, command.variables)
      self.state.active_dataset = next_dataset
      return TransformResult("Selected columns", next_dataset)

    if isinstance(command, RenameCommand):
      dataset = self._require_active_dataset("rename")
      next_dataset = self.backend.rename_column(dataset, command.old_name, command.new_name)
      self.state.active_dataset = next_dataset
      return TransformResult(f"Renamed {command.old_name} to {command.new_name}", next_dataset)

    if isinstance(command, GenerateCommand):
      dataset = self._require_active_dataset("generate")
      next_dataset = self.backend.generate_column(dataset, command.variable, command.expression)
      self.state.active_dataset = next_dataset
      return TransformResult(f"Generated {command.variable}", next_dataset)

    if isinstance(command, ReplaceCommand):
      dataset = self._require_active_dataset("replace")
      next_dataset = self.backend.replace_column(
        dataset,
        command.variable,
        command.expression,
        command.condition,
      )
      self.state.active_dataset = next_dataset
      return TransformResult(f"Replaced {command.variable}", next_dataset)

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
      dataset = self._require_active_dataset("collapse")
      next_dataset = self.backend.collapse(
        dataset,
        command.statistic,
        command.variables,
        command.groups,
      )
      self.state.active_dataset = next_dataset
      return TransformResult("Collapsed dataset", next_dataset)

    if isinstance(command, SqlCommand):
      dataset = self._require_active_dataset("sql")
      if command.into is not None:
        next_dataset = self.backend.replace_active_with_sql(dataset, command.query)
        self.state.active_dataset = next_dataset
        return SqlCreateResult(command.into, next_dataset)
      sql_headers, sql_rows = self.backend.run_sql(command.query)
      return TableResult(headers=sql_headers, rows=sql_rows)

    if isinstance(command, HistogramCommand):
      dataset = self._require_active_dataset("histogram")
      rows = self.backend.plot_rows(dataset, (command.variable,), numeric=True)
      path = command.saving or default_plot_path("histogram", (command.variable,))
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
      path = command.saving or default_plot_path("bar", (command.variable,))
      saved_path = save_bar(rows, command.variable, path)
      return PlotResult(path=saved_path, should_open=command.open_artifact)

    if isinstance(command, ByCommand):
      return self._execute_by(command)

    if isinstance(command, ExitCommand):
      return None

    raise ExecutionError("unsupported command")

  def _require_active_dataset(self, command_name: str) -> DatasetInfo:
    if self.state.active_dataset is None:
      raise ExecutionError(f"{command_name} requires an active dataset; run use <path> first")
    return self.state.active_dataset

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

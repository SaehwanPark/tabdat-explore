"""Command executor and session state."""

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, SupportsFloat, cast

import statsmodels.api as sm

from tabdat.backend import DuckDBBackend
from tabdat.config import TabDatConfig, set_config_value
from tabdat.errors import (
  ExecutionError,
  NoActiveDatasetError,
  TypeMismatchExecutionError,
  UnknownTableError,
  UnknownVariableError,
)
from tabdat.estimation import CoefficientEstimate
from tabdat.models import (
  ActivateResult,
  AppendCommand,
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
  ExportResult,
  GenerateCommand,
  HeadCommand,
  HistogramCommand,
  JoinCommand,
  KeepCommand,
  LoadResult,
  PanelCommand,
  PanelMetadata,
  PanelResult,
  PlotResult,
  PredictCommand,
  PreviewResult,
  RegressCommand,
  RegressionResult,
  RenameCommand,
  ReplaceCommand,
  ReshapeCommand,
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


@dataclass(frozen=True)
class _RegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  predictor_coefficients: tuple[float, ...]
  intercept: float | None


@dataclass
class SessionState:
  active_dataset: DatasetInfo | None = None
  active_table_name: str | None = None
  tables: dict[str, DatasetInfo] = field(default_factory=dict)
  config: TabDatConfig = TabDatConfig()
  regression: _RegressionState | None = None


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

    self._materialize_polars_lazy_if_needed(command)

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

    if isinstance(command, JoinCommand):
      return self._execute_join(command)

    if isinstance(command, AppendCommand):
      return self._execute_append(command)

    if isinstance(command, ReshapeCommand):
      return self._execute_reshape(command)

    if isinstance(command, PanelCommand):
      return self._execute_panel(command)

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

    if isinstance(command, SaveCommand):
      dataset = self._require_active_dataset("save")
      self.backend.save_active_parquet(command.path, replace=command.replace)
      saved_dataset = DatasetInfo(
        path=command.path,
        row_count=self.backend.active_row_count(),
        columns=dataset.columns,
        execution_mode="eager",
        lazy_engine=None,
        panel_metadata=dataset.panel_metadata,
      )
      return SaveResult(command.path, saved_dataset)

    if isinstance(command, ExportCommand):
      dataset = self._require_active_dataset("export")
      self.backend.export_active_dataset(command.path, replace=command.replace)
      exported_dataset = DatasetInfo(
        path=command.path,
        row_count=self.backend.active_row_count(),
        columns=dataset.columns,
        execution_mode="eager",
        lazy_engine=None,
        panel_metadata=dataset.panel_metadata,
      )
      return ExportResult(command.path, exported_dataset)

    if isinstance(command, RegressCommand):
      return self._execute_regress(command)

    if isinstance(command, PredictCommand):
      return self._execute_predict(command)

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
      table_name = _use_table_name(command)
      dataset = self.state.tables.get(table_name)
      if dataset is None:
        raise UnknownTableError(f"unknown table: {table_name}")
      activated = self.backend.activate_named_table(table_name)
      activated = replace(activated, panel_metadata=dataset.panel_metadata)
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
      next_dataset = _preserve_panel_metadata(dataset, next_dataset)
      return self._record_transform("Kept matching rows", next_dataset)
    next_dataset = self.backend.keep_columns(dataset, command.variables)
    next_dataset = _preserve_panel_metadata(dataset, next_dataset)
    return self._record_transform("Kept selected columns", next_dataset)

  def _execute_drop(self, command: DropCommand) -> TransformResult:
    dataset = self._require_active_dataset("drop")
    if command.condition is not None:
      next_dataset = self.backend.filter_rows(dataset, command.condition, keep=False)
      next_dataset = _preserve_panel_metadata(dataset, next_dataset)
      return self._record_transform("Dropped matching rows", next_dataset)
    next_dataset = self.backend.drop_columns(dataset, command.variables)
    next_dataset = _preserve_panel_metadata(dataset, next_dataset)
    return self._record_transform("Dropped selected columns", next_dataset)

  def _execute_select(self, command: SelectCommand) -> TransformResult:
    dataset = self._require_active_dataset("select")
    next_dataset = self.backend.keep_columns(dataset, command.variables)
    next_dataset = _preserve_panel_metadata(dataset, next_dataset)
    return self._record_transform("Selected columns", next_dataset)

  def _execute_rename(self, command: RenameCommand) -> TransformResult:
    dataset = self._require_active_dataset("rename")
    next_dataset = self.backend.rename_column(dataset, command.old_name, command.new_name)
    next_dataset = _rename_panel_metadata(dataset, next_dataset, command.old_name, command.new_name)
    return self._record_transform(f"Renamed {command.old_name} to {command.new_name}", next_dataset)

  def _execute_generate(self, command: GenerateCommand) -> TransformResult:
    dataset = self._require_active_dataset("generate")
    next_dataset = self.backend.generate_column(dataset, command.variable, command.expression)
    next_dataset = _preserve_panel_metadata(dataset, next_dataset)
    return self._record_transform(f"Generated {command.variable}", next_dataset)

  def _execute_replace(self, command: ReplaceCommand) -> TransformResult:
    dataset = self._require_active_dataset("replace")
    metadata = dataset.panel_metadata
    if _touches_panel_metadata(metadata, command.variable) and metadata is not None:
      next_dataset = self.backend.replace_column_with_panel_validation(
        dataset,
        command.variable,
        command.expression,
        command.condition,
        metadata,
      )
    else:
      next_dataset = self.backend.replace_column(
        dataset,
        command.variable,
        command.expression,
        command.condition,
      )
    next_dataset = _preserve_panel_metadata(dataset, next_dataset)
    return self._record_transform(f"Replaced {command.variable}", next_dataset)

  def _execute_collapse(self, command: CollapseCommand) -> TransformResult:
    dataset = self._require_active_dataset("collapse")
    next_dataset = self.backend.collapse(
      dataset,
      command.statistic,
      command.variables,
      command.groups,
    )
    return self._record_detached_transform("Collapsed dataset", next_dataset)

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

  def _execute_join(self, command: JoinCommand) -> TransformResult:
    active_dataset = self._require_active_dataset("join")
    right_dataset = self.state.tables.get(command.table_name)
    if right_dataset is None:
      raise UnknownTableError(f"unknown table: {command.table_name}")
    next_dataset = self.backend.join_named_table(
      active_dataset,
      right_dataset,
      table_name=command.table_name,
      keys=command.keys,
      how=command.how,
      suffix=command.suffix,
    )
    return self._record_transform(f"Joined {command.table_name}", next_dataset)

  def _execute_append(self, command: AppendCommand) -> TransformResult:
    active_dataset = self._require_active_dataset("append")
    append_dataset = self.state.tables.get(command.table_name)
    if append_dataset is None:
      raise UnknownTableError(f"unknown table: {command.table_name}")
    next_dataset = self.backend.append_named_table(
      active_dataset,
      append_dataset,
      table_name=command.table_name,
    )
    return self._record_detached_transform(f"Appended {command.table_name}", next_dataset)

  def _execute_reshape(self, command: ReshapeCommand) -> TransformResult:
    dataset = self._require_active_dataset("reshape")
    if command.direction == "long":
      next_dataset = self.backend.reshape_long(
        dataset,
        command.variables,
        command.identifiers,
        command.j_variable,
      )
      return self._record_detached_transform("Reshaped long", next_dataset)
    next_dataset = self.backend.reshape_wide(
      dataset,
      command.variables,
      command.identifiers,
      command.j_variable,
    )
    return self._record_detached_transform("Reshaped wide", next_dataset)

  def _execute_panel(self, command: PanelCommand) -> PanelResult:
    dataset = self._require_active_dataset("panel")
    if command.action == "report":
      return PanelResult(action="report", metadata=dataset.panel_metadata)
    if command.action == "clear":
      cleared = replace(dataset, panel_metadata=None)
      self._set_active_dataset(cleared)
      return PanelResult(action="clear")
    if command.id_variable is None or command.time_variable is None:
      raise ExecutionError("panel expects syntax: panel [<id_var> <time_var>|clear]")
    metadata = PanelMetadata(command.id_variable, command.time_variable)
    self.backend.validate_panel_metadata(dataset, metadata)
    updated = replace(dataset, panel_metadata=metadata)
    self._set_active_dataset(updated)
    return PanelResult(action="set", metadata=metadata)

  def _record_transform(self, message: str, dataset: DatasetInfo) -> TransformResult:
    self._set_active_dataset(dataset)
    return TransformResult(message, dataset)

  def _record_detached_transform(self, message: str, dataset: DatasetInfo) -> TransformResult:
    self.state.active_dataset = dataset
    self.state.active_table_name = None
    return TransformResult(message, dataset)

  def _execute_regress(self, command: RegressCommand) -> RegressionResult:
    dataset = self._require_active_dataset("regress")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    if command.weight_variable is not None:
      numeric_variables = (*numeric_variables, command.weight_variable)
    _require_numeric_columns(
      "regress",
      dataset,
      numeric_variables,
    )
    row_columns = [command.outcome, *command.predictors]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    if command.weight_variable is not None:
      row_columns.append(command.weight_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    outcome, predictors, groups, weights = _regression_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
      has_weight=command.weight_variable is not None,
      weight_label="weights" if command.estimator == "wls" else "sigma",
    )
    if not outcome:
      raise ExecutionError("regress requires at least one complete observation")
    design = _design_matrix(predictors, include_intercept=command.include_intercept)
    model = _regression_model(
      estimator=command.estimator,
      outcome=outcome,
      design=design,
      weights=weights,
    )
    fitted = model.fit()
    covariance = "nonrobust"
    if command.robust:
      fitted = fitted.get_robustcov_results(cov_type="HC1")
      covariance = "robust"
    if command.cluster_variable is not None:
      if groups is None:
        raise ExecutionError("regress requires complete cluster values")
      fitted = fitted.get_robustcov_results(cov_type="cluster", groups=groups)
      covariance = f"cluster({command.cluster_variable})"

    parameter_names = (
      ("intercept", *command.predictors) if command.include_intercept else command.predictors
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    intercept = coefficients[0].value if command.include_intercept else None
    predictor_coefficients = (
      tuple(estimate.value for estimate in coefficients[1:])
      if command.include_intercept
      else tuple(estimate.value for estimate in coefficients)
    )
    self.state.regression = _RegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      predictor_coefficients=predictor_coefficients,
      intercept=intercept,
    )
    return RegressionResult(
      outcome=command.outcome,
      predictors=command.predictors,
      estimator=command.estimator,
      covariance=covariance,
      observation_count=len(outcome),
      include_intercept=command.include_intercept,
      r_squared=_to_float(getattr(fitted, "rsquared", None)),
      adjusted_r_squared=_to_float(getattr(fitted, "rsquared_adj", None)),
      root_mse=_root_mse(
        mse_resid=getattr(fitted, "mse_resid", None),
        residuals=getattr(fitted, "resid", None),
        parameter_count=len(parameter_names),
      ),
      coefficients=coefficients,
    )

  def _execute_predict(self, command: PredictCommand) -> TransformResult:
    dataset = self._require_active_dataset("predict")
    regression = self.state.regression
    if regression is None:
      raise ExecutionError("predict requires a prior regress model")
    next_dataset = self.backend.add_linear_prediction_column(
      dataset,
      target_variable=command.target_variable,
      predictor_names=regression.predictor_names,
      predictor_coefficients=regression.predictor_coefficients,
      intercept=regression.intercept,
      outcome_variable=regression.outcome_variable,
      kind=command.kind,
    )
    return self._record_transform(f"Predicted {command.target_variable}", next_dataset)

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
      updated = replace(updated, panel_metadata=dataset.panel_metadata)
      self.state.active_dataset = updated
      self.state.tables[self.state.active_table_name] = updated
      return
    self.state.active_table_name = None

  def _should_activate_named_table(self, command: UseCommand) -> bool:
    if isinstance(command.path, str):
      return False
    table_name = _use_table_name(command)
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

  def _materialize_polars_lazy_if_needed(self, command: Command) -> None:
    if not self.backend.is_polars_lazy_active():
      return
    if isinstance(
      command,
      (
        DescribeCommand,
        CountCommand,
        HeadCommand,
        TailCommand,
        KeepCommand,
        DropCommand,
        SelectCommand,
        ExitCommand,
        SetCommand,
        SaveCommand,
        ExportCommand,
      ),
    ):
      return
    dataset = self._require_active_dataset("materialize")
    materialized = self.backend.materialize_polars_lazy(dataset.path)
    materialized = replace(materialized, panel_metadata=dataset.panel_metadata)
    self.state.active_dataset = materialized


def _require_numeric_columns(
  command_name: str,
  dataset: DatasetInfo,
  variables: tuple[str, ...],
) -> None:
  column_types = {column.name: column.data_type for column in dataset.columns}
  missing = tuple(variable for variable in variables if variable not in column_types)
  if missing:
    raise UnknownVariableError(f"{command_name} unknown variable: {', '.join(missing)}")
  non_numeric = tuple(
    variable for variable in variables if not _is_numeric_type(column_types[variable])
  )
  if non_numeric:
    raise TypeMismatchExecutionError(
      f"{command_name} requires numeric variables: {', '.join(non_numeric)}"
    )


def _regression_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
  has_cluster: bool,
  has_weight: bool,
  weight_label: str,
) -> tuple[
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[object, ...] | None,
  tuple[float, ...] | None,
]:
  outcomes: list[float] = []
  predictors: list[tuple[float, ...]] = []
  groups: list[object] = []
  weights: list[float] = []
  row_width = predictor_count + 1 + (1 if has_cluster else 0) + (1 if has_weight else 0)
  for row in rows:
    if len(row) != row_width:
      raise ExecutionError("regress failed")
    raw_outcome = row[0]
    raw_predictors = row[1 : 1 + predictor_count]
    index = 1 + predictor_count
    raw_group = row[index] if has_cluster else None
    if has_cluster:
      index += 1
    raw_weight = row[index] if has_weight else None
    if raw_outcome is None or any(value is None for value in raw_predictors):
      continue
    if has_cluster and raw_group is None:
      continue
    if has_weight and raw_weight is None:
      continue
    outcome = _coerce_float(raw_outcome)
    predictor_values = tuple(
      value
      for value in (_coerce_float(raw_value) for raw_value in raw_predictors)
      if value is not None
    )
    weight = _coerce_float(raw_weight) if has_weight else None
    if outcome is None or len(predictor_values) != predictor_count:
      continue
    if not math.isfinite(outcome) or any(not math.isfinite(value) for value in predictor_values):
      continue
    if has_weight:
      if weight is None:
        continue
      if weight <= 0.0:
        raise ExecutionError(f"regress requires positive {weight_label} values")
    outcomes.append(outcome)
    predictors.append(predictor_values)
    if has_cluster:
      groups.append(raw_group)
    if has_weight:
      assert weight is not None
      weights.append(weight)
  group_values = tuple(groups) if has_cluster else None
  weight_values = tuple(weights) if has_weight else None
  return tuple(outcomes), tuple(predictors), group_values, weight_values


def _regression_model(
  *,
  estimator: str,
  outcome: tuple[float, ...],
  design: list[list[float]],
  weights: tuple[float, ...] | None,
) -> Any:
  if estimator == "wls":
    if weights is None:
      raise ExecutionError("regress failed")
    return sm.WLS(outcome, design, weights=cast(Any, weights))
  if estimator == "gls":
    if weights is None:
      raise ExecutionError("regress failed")
    return sm.GLS(outcome, design, sigma=cast(Any, weights))
  return sm.OLS(outcome, design)


def _design_matrix(
  predictors: tuple[tuple[float, ...], ...],
  *,
  include_intercept: bool,
) -> list[list[float]]:
  if include_intercept:
    return [[1.0, *row] for row in predictors]
  return [list(row) for row in predictors]


def _coefficient_estimates(
  parameter_names: Sequence[str],
  fitted: object,
) -> tuple[CoefficientEstimate, ...]:
  params = _required_float_sequence(getattr(fitted, "params", None))
  standard_errors = _optional_float_sequence(getattr(fitted, "bse", None))
  statistics = _optional_float_sequence(getattr(fitted, "tvalues", None))
  p_values = _optional_float_sequence(getattr(fitted, "pvalues", None))
  if len(params) != len(parameter_names):
    raise ExecutionError("regress failed")
  return tuple(
    CoefficientEstimate(
      name=name,
      value=parameter,
      standard_error=_optional_sequence_value(standard_errors, index),
      statistic=_optional_sequence_value(statistics, index),
      p_value=_optional_sequence_value(p_values, index),
    )
    for index, (name, parameter) in enumerate(zip(parameter_names, params, strict=True))
  )


def _required_float_sequence(values: object) -> tuple[float, ...]:
  if values is None:
    return ()
  if isinstance(values, (str, bytes)):
    raise ExecutionError("regress failed")
  if not isinstance(values, Iterable):
    raise ExecutionError("regress failed")
  try:
    coerced = tuple(_coerce_float(value) for value in values)
  except (TypeError, ValueError) as exc:
    raise ExecutionError("regress failed") from exc
  if any(value is None for value in coerced):
    raise ExecutionError("regress failed")
  return tuple(value for value in coerced if value is not None)


def _optional_float_sequence(values: object) -> tuple[float | None, ...]:
  if values is None:
    return ()
  if isinstance(values, (str, bytes)):
    return ()
  if not isinstance(values, Iterable):
    return ()
  try:
    return tuple(_coerce_float(value) for value in values)
  except (TypeError, ValueError):
    return ()


def _optional_sequence_value(values: tuple[float | None, ...], index: int) -> float | None:
  if index >= len(values):
    return None
  value = values[index]
  if value is None or not math.isfinite(value):
    return None
  return value


def _to_float(value: object) -> float | None:
  numeric = _coerce_float(value)
  if numeric is None:
    return None
  if not math.isfinite(numeric):
    return None
  return numeric


def _root_mse(
  *,
  mse_resid: object,
  residuals: object,
  parameter_count: int,
) -> float | None:
  mse = _to_float(mse_resid)
  if mse is not None and mse >= 0.0:
    return math.sqrt(mse)
  if residuals is None:
    return None
  if isinstance(residuals, (str, bytes)):
    return None
  if not isinstance(residuals, Iterable):
    return None
  try:
    coerced = tuple(_coerce_float(value) for value in residuals)
  except (TypeError, ValueError):
    return None
  if any(value is None for value in coerced):
    return None
  values = tuple(value for value in coerced if value is not None)
  if len(values) <= parameter_count:
    return None
  rss = sum(value * value for value in values)
  df_resid = len(values) - parameter_count
  if df_resid <= 0:
    return None
  return math.sqrt(rss / df_resid)


def _coerce_float(value: object) -> float | None:
  if value is None or isinstance(value, bool):
    return None
  if not isinstance(value, SupportsFloat):
    return None
  try:
    numeric = float(value)
  except (TypeError, ValueError):
    return None
  if not math.isfinite(numeric):
    return None
  return numeric


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


def _use_table_name(command: UseCommand) -> str:
  if isinstance(command.path, str):
    return command.path
  return command.path.as_posix()


def _preserve_panel_metadata(previous: DatasetInfo, next_dataset: DatasetInfo) -> DatasetInfo:
  metadata = previous.panel_metadata
  if metadata is None:
    return next_dataset
  next_columns = {column.name for column in next_dataset.columns}
  if metadata.id_variable in next_columns and metadata.time_variable in next_columns:
    return replace(next_dataset, panel_metadata=metadata)
  return replace(next_dataset, panel_metadata=None)


def _rename_panel_metadata(
  previous: DatasetInfo,
  next_dataset: DatasetInfo,
  old_name: str,
  new_name: str,
) -> DatasetInfo:
  metadata = previous.panel_metadata
  if metadata is None:
    return next_dataset
  id_variable = new_name if metadata.id_variable == old_name else metadata.id_variable
  time_variable = new_name if metadata.time_variable == old_name else metadata.time_variable
  return replace(next_dataset, panel_metadata=PanelMetadata(id_variable, time_variable))


def _touches_panel_metadata(metadata: PanelMetadata | None, variable: str) -> bool:
  if metadata is None:
    return False
  return variable in {metadata.id_variable, metadata.time_variable}

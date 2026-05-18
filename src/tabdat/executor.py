"""Command executor and session state."""

import hashlib
import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, SupportsFloat, cast

import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS, IVGMM
from linearmodels.panel import PanelOLS, RandomEffects
from scipy.optimize import least_squares, minimize
from scipy.stats import chi2, norm
from statsmodels.discrete.count_model import ZeroInflatedNegativeBinomialP, ZeroInflatedPoisson
from statsmodels.stats.diagnostic import linear_reset
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor

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
  BinaryExpression,
  ByCommand,
  CfRegressCommand,
  CfRegressionResult,
  CodebookCommand,
  CodebookResult,
  CollapseCommand,
  Command,
  CountCommand,
  CountResult,
  DatasetInfo,
  DescribeCommand,
  DescribeResult,
  DidCommand,
  DidRegressionResult,
  DropCommand,
  EstatCommand,
  ExitCommand,
  ExportCommand,
  ExportResult,
  Expression,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HeckmanCommand,
  HeckmanRegressionResult,
  HistogramCommand,
  IdentifierExpression,
  IvRegressCommand,
  IvRegressionResult,
  JoinCommand,
  KeepCommand,
  LoadResult,
  LogitCommand,
  LogitRegressionResult,
  NbregCommand,
  NbregRegressionResult,
  NlCommand,
  NlRegressionResult,
  NumberExpression,
  PanelCommand,
  PanelMetadata,
  PanelResult,
  PlotResult,
  PoissonCommand,
  PoissonRegressionResult,
  PredictCommand,
  PreviewResult,
  ProbitCommand,
  ProbitRegressionResult,
  QregCommand,
  QregRegressionResult,
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
  StregCommand,
  StregRegressionResult,
  StringExpression,
  SummarizeCommand,
  SummarizeResult,
  TableResult,
  TabulateCommand,
  TailCommand,
  TobitCommand,
  TobitRegressionResult,
  TransformResult,
  UnaryExpression,
  UseCommand,
  XtAbondCommand,
  XtAbondRegressionResult,
  XtDataCommand,
  XtRegCommand,
  XtRegressionResult,
  ZinbCommand,
  ZinbRegressionResult,
  ZipCommand,
  ZipRegressionResult,
)
from tabdat.visualization import default_plot_path, save_bar, save_histogram, save_scatter


@dataclass(frozen=True)
class _RegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  predictor_coefficients: tuple[float, ...]
  intercept: float | None
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _QregRegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _IvRegressionState:
  estimator: Literal["2sls", "gmm"]
  fitted_model: object


@dataclass(frozen=True)
class _CfRegressionState:
  outcome_variable: str
  endogenous_variable: str
  first_stage_coefficients: tuple[CoefficientEstimate, ...]
  first_stage_predictor_names: tuple[str, ...]
  first_stage_predictor_coefficients: tuple[float, ...]
  first_stage_intercept: float | None
  first_stage_observation_count: int
  first_stage_r_squared: float | None
  second_stage_predictor_names: tuple[str, ...]
  second_stage_predictor_coefficients: tuple[float, ...]
  second_stage_intercept: float | None
  include_intercept: bool
  second_stage_residual_index: int
  residual_estimate: float | None
  residual_standard_error: float | None
  residual_statistic: float | None
  residual_p_value: float | None
  residual_ci_level: float | None
  residual_ci_lower: float | None
  residual_ci_upper: float | None
  residual_distribution: str | None
  residual_df: float | None


@dataclass(frozen=True)
class _XtRegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  panel_metadata: PanelMetadata
  estimator: str
  covariance: str
  cluster_variable: str | None
  sample_fingerprint: str
  fitted_model: object


@dataclass(frozen=True)
class _DidRegressionState:
  outcome_variable: str
  control_names: tuple[str, ...]
  treatment_variable: str
  post_variable: str
  fitted_model: object


@dataclass(frozen=True)
class _BinaryRegressionState:
  family: Literal["logit", "probit"]
  outcome_variable: str
  predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _NlRegressionState:
  outcome_variable: str
  parameter_names: tuple[str, ...]
  parameter_values: tuple[float, ...]
  include_intercept: bool
  expression: Expression
  predictor_names: tuple[str, ...]


@dataclass(frozen=True)
class _PoissonRegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _NbregRegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _ZipRegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  inflate_predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _ZinbRegressionState:
  outcome_variable: str
  predictor_names: tuple[str, ...]
  inflate_predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _StregRegressionState:
  time_variable: str
  predictor_names: tuple[str, ...]
  failure_variable: str
  distribution: Literal["weibull", "exponential"]
  include_intercept: bool
  fitted_model: object


@dataclass(frozen=True)
class _XtAbondFitResult:
  covariance: str
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass
class _XtModelCache:
  fe: _XtRegressionState | None = None
  re: _XtRegressionState | None = None


@dataclass
class SessionState:
  active_dataset: DatasetInfo | None = None
  active_table_name: str | None = None
  tables: dict[str, DatasetInfo] = field(default_factory=dict)
  config: TabDatConfig = TabDatConfig()
  regression: _RegressionState | None = None
  qreg_regression: _QregRegressionState | None = None
  binary_regression: _BinaryRegressionState | None = None
  nl_regression: _NlRegressionState | None = None
  poisson_regression: _PoissonRegressionState | None = None
  nbreg_regression: _NbregRegressionState | None = None
  zip_regression: _ZipRegressionState | None = None
  zinb_regression: _ZinbRegressionState | None = None
  streg_regression: _StregRegressionState | None = None
  iv_regression: _IvRegressionState | None = None
  cf_regression: _CfRegressionState | None = None
  xt_regressions: _XtModelCache = field(default_factory=_XtModelCache)
  did_regression: _DidRegressionState | None = None


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

    if isinstance(command, QregCommand):
      return self._execute_qreg(command)

    if isinstance(command, LogitCommand):
      return self._execute_logit(command)

    if isinstance(command, ProbitCommand):
      return self._execute_probit(command)

    if isinstance(command, TobitCommand):
      return self._execute_tobit(command)

    if isinstance(command, HeckmanCommand):
      return self._execute_heckman(command)

    if isinstance(command, NlCommand):
      return self._execute_nl(command)

    if isinstance(command, PoissonCommand):
      return self._execute_poisson(command)

    if isinstance(command, NbregCommand):
      return self._execute_nbreg(command)

    if isinstance(command, ZipCommand):
      return self._execute_zip(command)

    if isinstance(command, ZinbCommand):
      return self._execute_zinb(command)

    if isinstance(command, StregCommand):
      return self._execute_streg(command)

    if isinstance(command, IvRegressCommand):
      return self._execute_ivregress(command)

    if isinstance(command, CfRegressCommand):
      return self._execute_cfregress(command)

    if isinstance(command, XtRegCommand):
      return self._execute_xtreg(command)

    if isinstance(command, XtDataCommand):
      return self._execute_xtdata(command)

    if isinstance(command, XtAbondCommand):
      return self._execute_xtabond(command)

    if isinstance(command, DidCommand):
      return self._execute_did(command)

    if isinstance(command, PredictCommand):
      return self._execute_predict(command)

    if isinstance(command, EstatCommand):
      return self._execute_estat(command)

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
      metadata = dataset.panel_metadata
      if metadata is None:
        return PanelResult(action="report")
      summary = self.backend.panel_structure_summary(metadata)
      return PanelResult(action="report", metadata=metadata, summary=summary)
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
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
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

  def _execute_qreg(self, command: QregCommand) -> QregRegressionResult:
    dataset = self._require_active_dataset("qreg")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    _require_numeric_columns("qreg", dataset, numeric_variables)
    rows = self.backend.regression_rows(dataset, numeric_variables)
    outcome, predictors, _, _ = _regression_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=False,
      has_weight=False,
      weight_label="weights",
    )
    if not outcome:
      raise ExecutionError("qreg requires at least one complete observation")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcome, dtype=float)
    model = sm.QuantReg(outcome_array, design)
    covariance = "nonrobust"
    vcov = "iid"
    if command.robust:
      covariance = "robust"
      vcov = "robust"
    try:
      fitted = model.fit(q=command.quantile, vcov=vcov)
    except Exception as exc:
      raise ExecutionError("qreg failed") from exc
    parameter_names = (
      ("intercept", *command.predictors) if command.include_intercept else command.predictors
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.qreg_regression = _QregRegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return QregRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      quantile=command.quantile,
      observation_count=len(outcome),
      include_intercept=command.include_intercept,
      pseudo_r_squared=_to_float(getattr(fitted, "prsquared", None)),
      coefficients=coefficients,
    )

  def _execute_logit(self, command: LogitCommand) -> LogitRegressionResult:
    dataset = self._require_active_dataset("logit")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    _require_numeric_columns("logit", dataset, numeric_variables)
    row_columns = [command.outcome, *command.predictors]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    outcomes, predictors, groups, missing_cluster_detected = _logit_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("logit requires at least one complete observation")
    observed_outcomes = set(outcomes)
    if (
      observed_outcomes != {0.0, 1.0} and observed_outcomes != {0.0} and observed_outcomes != {1.0}
    ):
      raise ExecutionError("logit outcome must be binary with values 0 and 1")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcomes, dtype=float)
    covariance = "nonrobust"
    model = sm.Logit(outcome_array, design)
    try:
      if command.robust:
        fitted = model.fit(disp=0, cov_type="HC1")
        covariance = "robust"
      elif command.cluster_variable is not None:
        if groups is None or missing_cluster_detected:
          raise ExecutionError("logit requires complete cluster values")
        fitted = model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": np.array(groups)})
        covariance = f"cluster({command.cluster_variable})"
      else:
        fitted = model.fit(disp=0)
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("logit failed") from exc
    parameter_names = (
      ("intercept", *command.predictors) if command.include_intercept else command.predictors
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = _BinaryRegressionState(
      family="logit",
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.iv_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return LogitRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      pseudo_r_squared=_to_float(getattr(fitted, "prsquared", None)),
      coefficients=coefficients,
    )

  def _execute_probit(self, command: ProbitCommand) -> ProbitRegressionResult:
    dataset = self._require_active_dataset("probit")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    _require_numeric_columns("probit", dataset, numeric_variables)
    row_columns = [command.outcome, *command.predictors]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    outcomes, predictors, groups, missing_cluster_detected = _logit_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("probit requires at least one complete observation")
    observed_outcomes = set(outcomes)
    if (
      observed_outcomes != {0.0, 1.0} and observed_outcomes != {0.0} and observed_outcomes != {1.0}
    ):
      raise ExecutionError("probit outcome must be binary with values 0 and 1")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcomes, dtype=float)
    covariance = "nonrobust"
    model = sm.Probit(outcome_array, design)
    try:
      if command.robust:
        fitted = model.fit(disp=0, cov_type="HC1")
        covariance = "robust"
      elif command.cluster_variable is not None:
        if groups is None or missing_cluster_detected:
          raise ExecutionError("probit requires complete cluster values")
        fitted = model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": np.array(groups)})
        covariance = f"cluster({command.cluster_variable})"
      else:
        fitted = model.fit(disp=0)
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("probit failed") from exc
    parameter_names = (
      ("intercept", *command.predictors) if command.include_intercept else command.predictors
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = _BinaryRegressionState(
      family="probit",
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.iv_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return ProbitRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      pseudo_r_squared=_to_float(getattr(fitted, "prsquared", None)),
      coefficients=coefficients,
    )

  def _execute_ivregress(self, command: IvRegressCommand) -> IvRegressionResult:
    dataset = self._require_active_dataset("ivregress")
    numeric_variables: tuple[str, ...] = (
      command.outcome,
      *command.exogenous,
      command.endogenous,
      *command.instruments,
    )
    _require_numeric_columns("ivregress", dataset, numeric_variables)
    row_columns = [*numeric_variables]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    (
      outcomes,
      exogenous_values,
      endogenous_values,
      instrument_values,
      cluster_values,
    ) = _iv_regression_sample(
      rows=rows,
      exogenous_count=len(command.exogenous),
      instrument_count=len(command.instruments),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("ivregress requires at least one complete observation")
    exogenous_matrix = _design_matrix(exogenous_values, include_intercept=command.include_intercept)
    exog_data: Any = np.array(exogenous_matrix, dtype=float) if exogenous_matrix[0] else None
    dependent = np.array(outcomes, dtype=float)
    endogenous = np.array(endogenous_values, dtype=float)
    instruments = np.array(instrument_values, dtype=float)
    cov_type = "unadjusted"
    cov_label = "nonrobust"
    cov_config: dict[str, Any] = {}
    if command.robust:
      cov_type = "robust"
      cov_label = "robust"
    if command.cluster_variable is not None:
      cov_type = "clustered"
      cov_label = f"cluster({command.cluster_variable})"
      if cluster_values is None:
        raise ExecutionError("ivregress requires complete cluster values")
      cov_config["clusters"] = np.array(cluster_values)
    model: Any
    if command.estimator == "gmm":
      model = IVGMM(
        dependent=dependent,
        exog=exog_data,
        endog=endogenous,
        instruments=instruments,
      )
    else:
      model = IV2SLS(
        dependent=dependent,
        exog=exog_data,
        endog=endogenous,
        instruments=instruments,
      )
    try:
      fitted = model.fit(cov_type=cov_type, **cov_config)
    except Exception as exc:
      raise ExecutionError("ivregress failed") from exc
    parameter_names = _iv_parameter_names(command)
    coefficients = _iv_coefficient_estimates(parameter_names, fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = _IvRegressionState(
      estimator=command.estimator,
      fitted_model=fitted,
    )
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return IvRegressionResult(
      estimator=command.estimator,
      covariance=cov_label,
      outcome=command.outcome,
      exogenous=command.exogenous,
      endogenous=command.endogenous,
      instruments=command.instruments,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      r_squared=_to_float(getattr(fitted, "rsquared", None)),
      coefficients=coefficients,
    )

  def _execute_cfregress(self, command: CfRegressCommand) -> CfRegressionResult:
    dataset = self._require_active_dataset("cfregress")
    numeric_variables: tuple[str, ...] = (
      command.outcome,
      *command.exogenous,
      command.endogenous,
      *command.instruments,
    )
    _require_numeric_columns("cfregress", dataset, numeric_variables)
    row_columns = [*numeric_variables]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    (
      outcomes,
      exogenous_values,
      endogenous_values,
      instrument_values,
      cluster_values,
    ) = _iv_regression_sample(
      rows=rows,
      exogenous_count=len(command.exogenous),
      instrument_count=len(command.instruments),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("cfregress requires at least one complete observation")
    if command.cluster_variable is not None and cluster_values is None:
      raise ExecutionError("cfregress requires complete cluster values")

    first_stage_predictors = tuple(
      (*exogenous, *instruments)
      for exogenous, instruments in zip(exogenous_values, instrument_values, strict=True)
    )
    first_stage_design = _design_matrix(
      first_stage_predictors,
      include_intercept=command.include_intercept,
    )
    first_stage = sm.OLS(
      np.array(endogenous_values, dtype=float),
      np.array(first_stage_design, dtype=float),
    ).fit()
    first_stage_residuals = tuple(
      endog - fitted
      for endog, fitted in zip(
        endogenous_values,
        tuple(float(value) for value in first_stage.fittedvalues),
        strict=True,
      )
    )

    second_stage_predictors = tuple(
      (*exogenous, endogenous, residual)
      for exogenous, endogenous, residual in zip(
        exogenous_values,
        endogenous_values,
        first_stage_residuals,
        strict=True,
      )
    )
    second_stage_design = _design_matrix(
      second_stage_predictors,
      include_intercept=command.include_intercept,
    )
    fitted = sm.OLS(
      np.array(outcomes, dtype=float),
      np.array(second_stage_design, dtype=float),
    ).fit()
    covariance = "nonrobust"
    if command.robust:
      fitted = fitted.get_robustcov_results(cov_type="HC1")
      covariance = "robust"
    if command.cluster_variable is not None:
      assert cluster_values is not None
      fitted = fitted.get_robustcov_results(cov_type="cluster", groups=cluster_values)
      covariance = f"cluster({command.cluster_variable})"

    parameter_names = (
      ("intercept", *command.exogenous, command.endogenous, "cf_residual")
      if command.include_intercept
      else (*command.exogenous, command.endogenous, "cf_residual")
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    first_stage_parameter_names = (
      ("intercept", *command.exogenous, *command.instruments)
      if command.include_intercept
      else (*command.exogenous, *command.instruments)
    )
    first_stage_coefficients = _coefficient_estimates(first_stage_parameter_names, first_stage)
    first_stage_intercept = first_stage_coefficients[0].value if command.include_intercept else None
    first_stage_predictor_coefficients = (
      tuple(estimate.value for estimate in first_stage_coefficients[1:])
      if command.include_intercept
      else tuple(estimate.value for estimate in first_stage_coefficients)
    )
    second_stage_intercept = coefficients[0].value if command.include_intercept else None
    second_stage_predictor_coefficients = (
      tuple(estimate.value for estimate in coefficients[1:])
      if command.include_intercept
      else tuple(estimate.value for estimate in coefficients)
    )
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    (
      residual_estimate,
      residual_standard_error,
      residual_statistic,
      residual_p_value,
    ) = _cf_residual_diagnostic(
      coefficients=coefficients,
      include_intercept=command.include_intercept,
      residual_index=len(command.exogenous) + 1,
    )
    (
      residual_ci_lower,
      residual_ci_upper,
      residual_distribution,
      residual_df,
    ) = _cf_residual_confidence_interval(
      fitted_model=fitted,
      include_intercept=command.include_intercept,
      residual_index=len(command.exogenous) + 1,
    )
    self.state.cf_regression = _CfRegressionState(
      outcome_variable=command.outcome,
      endogenous_variable=command.endogenous,
      first_stage_coefficients=first_stage_coefficients,
      first_stage_predictor_names=(*command.exogenous, *command.instruments),
      first_stage_predictor_coefficients=first_stage_predictor_coefficients,
      first_stage_intercept=first_stage_intercept,
      first_stage_observation_count=len(endogenous_values),
      first_stage_r_squared=_to_float(getattr(first_stage, "rsquared", None)),
      second_stage_predictor_names=(*command.exogenous, command.endogenous, "cf_residual"),
      second_stage_predictor_coefficients=second_stage_predictor_coefficients,
      second_stage_intercept=second_stage_intercept,
      include_intercept=command.include_intercept,
      second_stage_residual_index=len(command.exogenous) + 1,
      residual_estimate=residual_estimate,
      residual_standard_error=residual_standard_error,
      residual_statistic=residual_statistic,
      residual_p_value=residual_p_value,
      residual_ci_level=95.0,
      residual_ci_lower=residual_ci_lower,
      residual_ci_upper=residual_ci_upper,
      residual_distribution=residual_distribution,
      residual_df=residual_df,
    )
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return CfRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      exogenous=command.exogenous,
      endogenous=command.endogenous,
      instruments=command.instruments,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      r_squared=_to_float(getattr(fitted, "rsquared", None)),
      coefficients=coefficients,
    )

  def _execute_nl(self, command: NlCommand) -> NlRegressionResult:
    dataset = self._require_active_dataset("nl")
    predictor_names = _nl_predictor_names(command.expression, command.parameter_names)
    if command.outcome in command.parameter_names:
      raise ExecutionError("nl outcome must not appear in params")
    variables = (command.outcome, *predictor_names)
    _require_numeric_columns("nl", dataset, variables)
    rows = self.backend.regression_rows(dataset, variables)
    outcomes, predictors = _nl_sample(rows=rows, predictor_count=len(predictor_names))
    if not outcomes:
      raise ExecutionError("nl requires at least one complete observation")
    predictor_index = {name: index for index, name in enumerate(predictor_names)}
    param_index = {name: index for index, name in enumerate(command.parameter_names)}
    initial = np.array(command.start_values, dtype=float)
    outcome_array = np.array(outcomes, dtype=float)

    def residual_fn(params: np.ndarray) -> np.ndarray:
      predicted = np.array(
        [
          _evaluate_nl_expression(
            command.expression,
            predictor_row=row,
            predictor_index=predictor_index,
            params=params,
            param_index=param_index,
          )
          for row in predictors
        ],
        dtype=float,
      )
      residuals = np.asarray(outcome_array - predicted, dtype=float)
      return cast(np.ndarray, residuals)

    try:
      fit = least_squares(residual_fn, x0=initial)
    except Exception as exc:
      raise ExecutionError("nl failed") from exc
    if not fit.success:
      raise ExecutionError("nl failed")

    residuals = residual_fn(fit.x)
    jacobian = np.array(fit.jac, dtype=float)
    covariance, covariance_label = _nl_covariance_matrix(
      jacobian=jacobian,
      residuals=np.array(residuals, dtype=float),
      robust=command.robust,
    )
    coefficients = _nl_coefficient_estimates(
      parameter_names=command.parameter_names,
      values=np.array(fit.x, dtype=float),
      covariance=covariance,
      residual_df=max(len(outcomes) - len(command.parameter_names), 1),
    )
    rss = float(np.dot(residuals, residuals))
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = _NlRegressionState(
      outcome_variable=command.outcome,
      parameter_names=command.parameter_names,
      parameter_values=tuple(float(value) for value in fit.x),
      include_intercept=command.include_intercept,
      expression=command.expression,
      predictor_names=predictor_names,
    )
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return NlRegressionResult(
      covariance=covariance_label,
      outcome=command.outcome,
      expression=_format_expression(command.expression),
      parameter_names=command.parameter_names,
      observation_count=len(outcomes),
      residual_sum_of_squares=rss,
      coefficients=coefficients,
    )

  def _execute_poisson(self, command: PoissonCommand) -> PoissonRegressionResult:
    dataset = self._require_active_dataset("poisson")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    _require_numeric_columns("poisson", dataset, numeric_variables)
    row_columns = [command.outcome, *command.predictors]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    outcomes, predictors, groups, missing_cluster_detected = _logit_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("poisson requires at least one complete observation")
    if any(outcome < 0 for outcome in outcomes):
      raise ExecutionError("poisson outcome must be non-negative")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcomes, dtype=float)
    covariance = "nonrobust"
    model = sm.Poisson(outcome_array, design)
    try:
      if command.robust:
        fitted = model.fit(disp=0, cov_type="HC1")
        covariance = "robust"
      elif command.cluster_variable is not None:
        if groups is None or missing_cluster_detected:
          raise ExecutionError("poisson requires complete cluster values")
        fitted = model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": np.array(groups)})
        covariance = f"cluster({command.cluster_variable})"
      else:
        fitted = model.fit(disp=0)
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("poisson failed") from exc
    parameter_names = (
      ("intercept", *command.predictors) if command.include_intercept else command.predictors
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = _PoissonRegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return PoissonRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      log_likelihood=_to_float(getattr(fitted, "llf", None)),
      coefficients=coefficients,
    )

  def _execute_nbreg(self, command: NbregCommand) -> NbregRegressionResult:
    dataset = self._require_active_dataset("nbreg")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    _require_numeric_columns("nbreg", dataset, numeric_variables)
    row_columns = [command.outcome, *command.predictors]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    outcomes, predictors, groups, missing_cluster_detected = _logit_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("nbreg requires at least one complete observation")
    if any(outcome < 0 for outcome in outcomes):
      raise ExecutionError("nbreg outcome must be non-negative")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcomes, dtype=float)
    covariance = "nonrobust"
    model = sm.NegativeBinomial(outcome_array, design)
    try:
      if command.robust:
        fitted = model.fit(disp=0, cov_type="HC1")
        covariance = "robust"
      elif command.cluster_variable is not None:
        if groups is None or missing_cluster_detected:
          raise ExecutionError("nbreg requires complete cluster values")
        fitted = model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": np.array(groups)})
        covariance = f"cluster({command.cluster_variable})"
      else:
        fitted = model.fit(disp=0)
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("nbreg failed") from exc
    parameter_names = (
      ("intercept", *command.predictors, "lnalpha")
      if command.include_intercept
      else (*command.predictors, "lnalpha")
    )
    coefficients = _coefficient_estimates(parameter_names, fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = _NbregRegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return NbregRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      log_likelihood=_to_float(getattr(fitted, "llf", None)),
      coefficients=coefficients,
    )

  def _execute_zip(self, command: ZipCommand) -> ZipRegressionResult:
    dataset = self._require_active_dataset("zip")
    numeric_variables: tuple[str, ...] = (
      command.outcome,
      *command.predictors,
      *command.inflate_predictors,
    )
    _require_numeric_columns("zip", dataset, numeric_variables)
    rows = self.backend.regression_rows(
      dataset,
      _zero_inflated_row_columns(
        outcome=command.outcome,
        predictors=command.predictors,
        inflate_predictors=command.inflate_predictors,
        cluster_variable=command.cluster_variable,
      ),
    )
    outcomes, predictors, inflation_predictors, groups, missing_cluster_detected = (
      _zero_inflated_sample(
        rows=rows,
        predictor_count=len(command.predictors),
        inflate_predictor_count=len(command.inflate_predictors),
        has_cluster=command.cluster_variable is not None,
      )
    )
    if not outcomes:
      raise ExecutionError("zip requires at least one complete observation")
    if any(outcome < 0 for outcome in outcomes):
      raise ExecutionError("zip outcome must be non-negative")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    inflation_design = np.array(
      _design_matrix(inflation_predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcomes, dtype=float)
    covariance = "nonrobust"
    model = ZeroInflatedPoisson(
      endog=outcome_array,
      exog=design,
      exog_infl=inflation_design,
      inflation="logit",
    )
    try:
      if command.robust:
        fitted = model.fit(disp=0, cov_type="HC1")
        covariance = "robust"
      elif command.cluster_variable is not None:
        if groups is None or missing_cluster_detected:
          raise ExecutionError("zip requires complete cluster values")
        fitted = model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": np.array(groups)})
        covariance = f"cluster({command.cluster_variable})"
      else:
        fitted = model.fit(disp=0)
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("zip failed") from exc
    coefficients = _coefficient_estimates(_fitted_parameter_names(fitted), fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = _ZipRegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      inflate_predictor_names=command.inflate_predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return ZipRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      inflate_predictors=command.inflate_predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      log_likelihood=_to_float(getattr(fitted, "llf", None)),
      coefficients=coefficients,
    )

  def _execute_zinb(self, command: ZinbCommand) -> ZinbRegressionResult:
    dataset = self._require_active_dataset("zinb")
    numeric_variables: tuple[str, ...] = (
      command.outcome,
      *command.predictors,
      *command.inflate_predictors,
    )
    _require_numeric_columns("zinb", dataset, numeric_variables)
    rows = self.backend.regression_rows(
      dataset,
      _zero_inflated_row_columns(
        outcome=command.outcome,
        predictors=command.predictors,
        inflate_predictors=command.inflate_predictors,
        cluster_variable=command.cluster_variable,
      ),
    )
    outcomes, predictors, inflation_predictors, groups, missing_cluster_detected = (
      _zero_inflated_sample(
        rows=rows,
        predictor_count=len(command.predictors),
        inflate_predictor_count=len(command.inflate_predictors),
        has_cluster=command.cluster_variable is not None,
      )
    )
    if not outcomes:
      raise ExecutionError("zinb requires at least one complete observation")
    if any(outcome < 0 for outcome in outcomes):
      raise ExecutionError("zinb outcome must be non-negative")
    design = np.array(
      _design_matrix(predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    inflation_design = np.array(
      _design_matrix(inflation_predictors, include_intercept=command.include_intercept),
      dtype=float,
    )
    outcome_array = np.array(outcomes, dtype=float)
    covariance = "nonrobust"
    model = ZeroInflatedNegativeBinomialP(
      endog=outcome_array,
      exog=design,
      exog_infl=inflation_design,
      inflation="logit",
    )
    try:
      if command.robust:
        fitted = model.fit(disp=0, cov_type="HC1")
        covariance = "robust"
      elif command.cluster_variable is not None:
        if groups is None or missing_cluster_detected:
          raise ExecutionError("zinb requires complete cluster values")
        fitted = model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": np.array(groups)})
        covariance = f"cluster({command.cluster_variable})"
      else:
        fitted = model.fit(disp=0)
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("zinb failed") from exc
    coefficients = _coefficient_estimates(_fitted_parameter_names(fitted), fitted)
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = _ZinbRegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      inflate_predictor_names=command.inflate_predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.iv_regression = None
    self.state.streg_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return ZinbRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      inflate_predictors=command.inflate_predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      log_likelihood=_to_float(getattr(fitted, "llf", None)),
      coefficients=coefficients,
    )

  def _execute_predict(self, command: PredictCommand) -> TransformResult:
    dataset = self._require_active_dataset("predict")
    if command.kind == "pr":
      binary_regression = self.state.binary_regression
      if binary_regression is None:
        raise ExecutionError("predict option pr requires a prior logit or probit model")
      available_columns = {column.name for column in dataset.columns}
      if any(name not in available_columns for name in binary_regression.predictor_names):
        raise ExecutionError("predict option pr requires a prior logit or probit model")
      rows = self.backend.regression_rows(dataset, binary_regression.predictor_names)
      predictions = _binary_predictions(
        rows=rows,
        fitted_model=binary_regression.fitted_model,
        predictor_count=len(binary_regression.predictor_names),
        include_intercept=binary_regression.include_intercept,
        kind="pr",
      )
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    binary_regression = self.state.binary_regression
    if binary_regression is not None:
      if command.kind == "residuals":
        raise ExecutionError("predict residuals is not available after logit or probit")
      rows = self.backend.regression_rows(dataset, binary_regression.predictor_names)
      predictions = _binary_predictions(
        rows=rows,
        fitted_model=binary_regression.fitted_model,
        predictor_count=len(binary_regression.predictor_names),
        include_intercept=binary_regression.include_intercept,
        kind="xb",
      )
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    regression = self.state.regression
    if regression is not None:
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
    qreg_regression = self.state.qreg_regression
    if qreg_regression is not None:
      available_columns = {column.name for column in dataset.columns}
      if any(name not in available_columns for name in qreg_regression.predictor_names):
        raise ExecutionError("predict requires a prior qreg model with matching variables")
      rows = self.backend.regression_rows(dataset, qreg_regression.predictor_names)
      qreg_predictions = _qreg_predictions(
        rows=rows,
        fitted_model=qreg_regression.fitted_model,
        predictor_count=len(qreg_regression.predictor_names),
        include_intercept=qreg_regression.include_intercept,
      )
      if command.kind == "residuals":
        outcomes = self.backend.regression_rows(dataset, (qreg_regression.outcome_variable,))
        qreg_residuals: list[float | None] = []
        for outcome_row, predicted_value in zip(outcomes, qreg_predictions, strict=True):
          if predicted_value is None or len(outcome_row) != 1:
            qreg_residuals.append(None)
            continue
          observed = _coerce_float(outcome_row[0])
          if observed is None:
            qreg_residuals.append(None)
            continue
          qreg_residuals.append(observed - predicted_value)
        qreg_predictions = tuple(qreg_residuals)
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=qreg_predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    did_regression = self.state.did_regression
    if did_regression is not None:
      if command.kind != "xb":
        raise ExecutionError("predict only supports xb after did")
      panel_metadata = dataset.panel_metadata
      if panel_metadata is None:
        raise ExecutionError("predict requires a prior did model with matching variables")
      required_columns = (
        panel_metadata.id_variable,
        panel_metadata.time_variable,
        did_regression.outcome_variable,
        *did_regression.control_names,
        did_regression.treatment_variable,
        did_regression.post_variable,
      )
      available_columns = {column.name for column in dataset.columns}
      if any(name not in available_columns for name in required_columns):
        raise ExecutionError("predict requires a prior did model with matching variables")
      rows = self.backend.regression_rows(dataset, required_columns)
      predictions = _did_predictions(
        rows=rows,
        id_variable=panel_metadata.id_variable,
        time_variable=panel_metadata.time_variable,
        control_names=did_regression.control_names,
        fitted_model=did_regression.fitted_model,
      )
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    cf_regression = self.state.cf_regression
    if cf_regression is not None:
      next_dataset = self.backend.add_cf_prediction_column(
        dataset,
        target_variable=command.target_variable,
        first_stage_predictor_names=cf_regression.first_stage_predictor_names,
        first_stage_predictor_coefficients=cf_regression.first_stage_predictor_coefficients,
        first_stage_intercept=cf_regression.first_stage_intercept,
        second_stage_predictor_names=cf_regression.second_stage_predictor_names,
        second_stage_predictor_coefficients=cf_regression.second_stage_predictor_coefficients,
        second_stage_intercept=cf_regression.second_stage_intercept,
        second_stage_residual_index=cf_regression.second_stage_residual_index,
        endogenous_variable=cf_regression.endogenous_variable,
        outcome_variable=cf_regression.outcome_variable,
        kind=command.kind,
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    nl_regression = self.state.nl_regression
    if nl_regression is not None:
      available_columns = {column.name for column in dataset.columns}
      if any(name not in available_columns for name in nl_regression.predictor_names):
        raise ExecutionError("predict requires a prior nl model with matching variables")
      if nl_regression.predictor_names:
        rows = self.backend.regression_rows(dataset, nl_regression.predictor_names)
        predicted = _nl_predictions(
          expression=nl_regression.expression,
          rows=rows,
          predictor_names=nl_regression.predictor_names,
          parameter_names=nl_regression.parameter_names,
          parameter_values=nl_regression.parameter_values,
        )
      else:
        predicted = _nl_constant_predictions(
          expression=nl_regression.expression,
          parameter_names=nl_regression.parameter_names,
          parameter_values=nl_regression.parameter_values,
          row_count=self.backend.active_row_count(),
        )
      if command.kind == "residuals":
        outcomes = self.backend.regression_rows(dataset, (nl_regression.outcome_variable,))
        residual_values: list[float | None] = []
        for outcome, value in zip(outcomes, predicted, strict=True):
          if value is None or len(outcome) != 1:
            residual_values.append(None)
            continue
          outcome_value = _coerce_float(outcome[0])
          if outcome_value is None:
            residual_values.append(None)
            continue
          residual_values.append(outcome_value - value)
        predicted = tuple(residual_values)
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=predicted,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    poisson_regression = self.state.poisson_regression
    if poisson_regression is not None:
      available_columns = {column.name for column in dataset.columns}
      if any(name not in available_columns for name in poisson_regression.predictor_names):
        raise ExecutionError("predict requires a prior poisson model with matching variables")
      rows = self.backend.regression_rows(dataset, poisson_regression.predictor_names)
      poisson_predictions = _poisson_predictions(
        rows=rows,
        fitted_model=poisson_regression.fitted_model,
        predictor_count=len(poisson_regression.predictor_names),
        include_intercept=poisson_regression.include_intercept,
        kind="xb" if command.kind == "xb" else "mean",
      )
      if command.kind == "residuals":
        outcomes = self.backend.regression_rows(dataset, (poisson_regression.outcome_variable,))
        residuals: list[float | None] = []
        for outcome_row, predicted_value in zip(outcomes, poisson_predictions, strict=True):
          if predicted_value is None or len(outcome_row) != 1:
            residuals.append(None)
            continue
          observed = _coerce_float(outcome_row[0])
          if observed is None:
            residuals.append(None)
            continue
          residuals.append(observed - predicted_value)
        poisson_predictions = tuple(residuals)
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=poisson_predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    nbreg_regression = self.state.nbreg_regression
    if nbreg_regression is not None:
      available_columns = {column.name for column in dataset.columns}
      if any(name not in available_columns for name in nbreg_regression.predictor_names):
        raise ExecutionError("predict requires a prior nbreg model with matching variables")
      rows = self.backend.regression_rows(dataset, nbreg_regression.predictor_names)
      nbreg_predictions = _nbreg_predictions(
        rows=rows,
        fitted_model=nbreg_regression.fitted_model,
        predictor_count=len(nbreg_regression.predictor_names),
        include_intercept=nbreg_regression.include_intercept,
        kind="xb" if command.kind == "xb" else "mean",
      )
      if command.kind == "residuals":
        outcomes = self.backend.regression_rows(dataset, (nbreg_regression.outcome_variable,))
        nbreg_residuals: list[float | None] = []
        for outcome_row, predicted_value in zip(outcomes, nbreg_predictions, strict=True):
          if predicted_value is None or len(outcome_row) != 1:
            nbreg_residuals.append(None)
            continue
          observed = _coerce_float(outcome_row[0])
          if observed is None:
            nbreg_residuals.append(None)
            continue
          nbreg_residuals.append(observed - predicted_value)
        nbreg_predictions = tuple(nbreg_residuals)
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=nbreg_predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    zip_regression = self.state.zip_regression
    if zip_regression is not None:
      available_columns = {column.name for column in dataset.columns}
      required = (*zip_regression.predictor_names, *zip_regression.inflate_predictor_names)
      if any(name not in available_columns for name in required):
        raise ExecutionError("predict requires a prior zip model with matching variables")
      rows = self.backend.regression_rows(dataset, zip_regression.predictor_names)
      inflation_rows = self.backend.regression_rows(dataset, zip_regression.inflate_predictor_names)
      zip_predictions = _zero_inflated_predictions(
        rows=rows,
        inflation_rows=inflation_rows,
        fitted_model=zip_regression.fitted_model,
        predictor_count=len(zip_regression.predictor_names),
        inflate_predictor_count=len(zip_regression.inflate_predictor_names),
        include_intercept=zip_regression.include_intercept,
        kind="xb" if command.kind == "xb" else "mean",
      )
      if command.kind == "residuals":
        outcomes = self.backend.regression_rows(dataset, (zip_regression.outcome_variable,))
        zip_residuals: list[float | None] = []
        for outcome_row, predicted_value in zip(outcomes, zip_predictions, strict=True):
          if predicted_value is None or len(outcome_row) != 1:
            zip_residuals.append(None)
            continue
          observed = _coerce_float(outcome_row[0])
          if observed is None:
            zip_residuals.append(None)
            continue
          zip_residuals.append(observed - predicted_value)
        zip_predictions = tuple(zip_residuals)
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=zip_predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    zinb_regression = self.state.zinb_regression
    if zinb_regression is not None:
      available_columns = {column.name for column in dataset.columns}
      required = (*zinb_regression.predictor_names, *zinb_regression.inflate_predictor_names)
      if any(name not in available_columns for name in required):
        raise ExecutionError("predict requires a prior zinb model with matching variables")
      rows = self.backend.regression_rows(dataset, zinb_regression.predictor_names)
      inflation_rows = self.backend.regression_rows(
        dataset,
        zinb_regression.inflate_predictor_names,
      )
      zinb_predictions = _zero_inflated_predictions(
        rows=rows,
        inflation_rows=inflation_rows,
        fitted_model=zinb_regression.fitted_model,
        predictor_count=len(zinb_regression.predictor_names),
        inflate_predictor_count=len(zinb_regression.inflate_predictor_names),
        include_intercept=zinb_regression.include_intercept,
        kind="xb" if command.kind == "xb" else "mean",
      )
      if command.kind == "residuals":
        outcomes = self.backend.regression_rows(dataset, (zinb_regression.outcome_variable,))
        zinb_residuals: list[float | None] = []
        for outcome_row, predicted_value in zip(outcomes, zinb_predictions, strict=True):
          if predicted_value is None or len(outcome_row) != 1:
            zinb_residuals.append(None)
            continue
          observed = _coerce_float(outcome_row[0])
          if observed is None:
            zinb_residuals.append(None)
            continue
          zinb_residuals.append(observed - predicted_value)
        zinb_predictions = tuple(zinb_residuals)
      next_dataset = self.backend.add_numeric_column_from_values(
        dataset,
        target_variable=command.target_variable,
        values=zinb_predictions,
        command_name="predict",
      )
      return self._record_transform(f"Predicted {command.target_variable}", next_dataset)
    raise ExecutionError(
      "predict requires a prior regress, qreg, did, cfregress, nl, poisson, nbreg, zip, "
      "or zinb model"
    )

  def _execute_streg(self, command: StregCommand) -> StregRegressionResult:
    dataset = self._require_active_dataset("streg")
    numeric_variables: tuple[str, ...] = (
      command.time_variable,
      command.failure_variable,
      *command.predictors,
    )
    _require_numeric_columns("streg", dataset, numeric_variables)
    row_columns = [*numeric_variables]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    times, failures, predictors, groups, missing_cluster_detected = _streg_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if not times:
      raise ExecutionError("streg requires at least one complete observation")
    if any(time <= 0.0 for time in times):
      raise ExecutionError("streg time variable must be strictly positive")
    observed_failures = set(failures)
    if (
      observed_failures != {0.0, 1.0} and observed_failures != {0.0} and observed_failures != {1.0}
    ):
      raise ExecutionError("streg failure variable must be binary with values 0 and 1")
    if command.cluster_variable is not None and (groups is None or missing_cluster_detected):
      raise ExecutionError("streg requires complete cluster values")
    try:
      covariance, coefficients = _fit_streg_parametric(
        times=times,
        failures=failures,
        predictors=predictors,
        predictor_names=command.predictors,
        include_intercept=command.include_intercept,
        distribution=command.distribution,
        robust=command.robust,
        cluster_values=groups,
        cluster_variable=command.cluster_variable,
      )
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("streg failed") from exc
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = _StregRegressionState(
      time_variable=command.time_variable,
      predictor_names=command.predictors,
      failure_variable=command.failure_variable,
      distribution=command.distribution,
      include_intercept=command.include_intercept,
      fitted_model=coefficients,
    )
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return StregRegressionResult(
      covariance=covariance,
      time_variable=command.time_variable,
      predictors=command.predictors,
      failure_variable=command.failure_variable,
      distribution=command.distribution,
      observation_count=len(times),
      include_intercept=command.include_intercept,
      coefficients=coefficients,
    )

  def _execute_tobit(self, command: TobitCommand) -> TobitRegressionResult:
    if command.upper_limit is not None and command.lower_limit >= command.upper_limit:
      raise ExecutionError("tobit lower limit must be less than upper limit")
    dataset = self._require_active_dataset("tobit")
    numeric_variables: tuple[str, ...] = (command.outcome, *command.predictors)
    _require_numeric_columns("tobit", dataset, numeric_variables)
    row_columns = [command.outcome, *command.predictors]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    outcomes, predictors, groups, missing_cluster_detected = _logit_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if not outcomes:
      raise ExecutionError("tobit requires at least one complete observation")
    if command.cluster_variable is not None and (groups is None or missing_cluster_detected):
      raise ExecutionError("tobit requires complete cluster values")
    try:
      covariance, coefficients = _fit_tobit_with_r(
        outcomes=outcomes,
        predictors=predictors,
        predictor_names=command.predictors,
        include_intercept=command.include_intercept,
        lower_limit=command.lower_limit,
        upper_limit=command.upper_limit,
        robust=command.robust,
        cluster_values=groups,
        cluster_variable=command.cluster_variable,
      )
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("tobit failed") from exc
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return TobitRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      lower_limit=command.lower_limit,
      upper_limit=command.upper_limit,
      coefficients=coefficients,
    )

  def _execute_heckman(self, command: HeckmanCommand) -> HeckmanRegressionResult:
    dataset = self._require_active_dataset("heckman")
    numeric_variables: tuple[str, ...] = (
      command.outcome,
      *command.predictors,
      command.selection_dependent,
      *command.selection_predictors,
    )
    _require_numeric_columns("heckman", dataset, numeric_variables)
    row_columns = [*numeric_variables]
    if command.cluster_variable is not None:
      row_columns.append(command.cluster_variable)
    rows = self.backend.regression_rows(dataset, tuple(row_columns))
    sample = _heckman_sample(
      rows=rows,
      outcome_predictor_count=len(command.predictors),
      selection_predictor_count=len(command.selection_predictors),
      has_cluster=command.cluster_variable is not None,
    )
    (
      outcomes,
      outcome_predictors,
      selection_outcomes,
      selection_predictors,
      clusters,
      missing_cluster_detected,
    ) = sample
    if not outcomes:
      raise ExecutionError("heckman requires at least one complete observation")
    if command.cluster_variable is not None and (clusters is None or missing_cluster_detected):
      raise ExecutionError("heckman requires complete cluster values")
    observed_selections = set(selection_outcomes)
    if (
      observed_selections != {0.0, 1.0}
      and observed_selections != {0.0}
      and observed_selections != {1.0}
    ):
      raise ExecutionError(
        "heckman selection dependent variable must be binary with values 0 and 1"
      )
    try:
      covariance, outcome_coefficients, selection_coefficients = _fit_heckman_with_r(
        outcomes=outcomes,
        outcome_predictors=outcome_predictors,
        outcome_predictor_names=command.predictors,
        selection_outcomes=selection_outcomes,
        selection_predictors=selection_predictors,
        selection_predictor_names=command.selection_predictors,
        include_intercept=command.include_intercept,
        robust=command.robust,
        cluster_values=clusters,
        cluster_variable=command.cluster_variable,
      )
    except ExecutionError:
      raise
    except Exception as exc:
      raise ExecutionError("heckman failed") from exc
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return HeckmanRegressionResult(
      covariance=covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      selection_dependent=command.selection_dependent,
      selection_predictors=command.selection_predictors,
      observation_count=len(outcomes),
      include_intercept=command.include_intercept,
      outcome_coefficients=outcome_coefficients,
      selection_coefficients=selection_coefficients,
    )

  def _execute_estat(self, command: EstatCommand) -> TableResult:
    dataset = self._require_active_dataset("estat")
    if command.subcommand == "residuals":
      regression = self.state.regression
      if regression is not None:
        return _estat_residuals_table(regression.fitted_model)
      qreg_regression = self.state.qreg_regression
      if qreg_regression is not None:
        return _estat_residuals_table(qreg_regression.fitted_model)
      raise ExecutionError("estat residuals requires a prior regress or qreg model")
    if command.subcommand == "ovtest":
      regression = self.state.regression
      if regression is None:
        raise ExecutionError("estat requires a prior regress model")
      return _estat_ovtest_table(regression.fitted_model)
    if command.subcommand == "vif":
      regression = self.state.regression
      if regression is None:
        raise ExecutionError("estat requires a prior regress model")
      return _estat_vif_table(
        regression.fitted_model,
        predictor_names=regression.predictor_names,
        include_intercept=regression.include_intercept,
      )
    if command.subcommand == "firststage":
      iv_regression = self.state.iv_regression
      if iv_regression is not None:
        return _estat_iv_firststage_table(iv_regression.fitted_model)
      cf_regression = self.state.cf_regression
      if cf_regression is not None:
        return _estat_cf_firststage_table(cf_regression)
      raise ExecutionError("estat firststage requires a prior ivregress model")
    if command.subcommand == "overid":
      iv_regression = self.state.iv_regression
      if iv_regression is None:
        raise ExecutionError("estat overid requires a prior ivregress model")
      return _estat_iv_overid_table(iv_regression.fitted_model)
    if command.subcommand == "hausman":
      fe_state = self.state.xt_regressions.fe
      re_state = self.state.xt_regressions.re
      if fe_state is None or re_state is None:
        raise ExecutionError("estat hausman requires prior xtreg fe and xtreg re models")
      if fe_state.cluster_variable is not None or re_state.cluster_variable is not None:
        raise ExecutionError("estat hausman does not support clustered covariance")
      if fe_state.outcome_variable != re_state.outcome_variable:
        raise ExecutionError("estat hausman requires matching xtreg specifications")
      if fe_state.predictor_names != re_state.predictor_names:
        raise ExecutionError("estat hausman requires matching xtreg specifications")
      if fe_state.panel_metadata != re_state.panel_metadata:
        raise ExecutionError("estat hausman requires matching xtreg specifications")
      if fe_state.covariance != re_state.covariance:
        raise ExecutionError("estat hausman requires matching xtreg covariance modes")
      if fe_state.sample_fingerprint != re_state.sample_fingerprint:
        raise ExecutionError("estat hausman requires matching xtreg estimation sample")
      if dataset.panel_metadata != fe_state.panel_metadata:
        raise ExecutionError("estat hausman requires matching panel metadata")
      return _estat_hausman_table(fe_state.fitted_model, re_state.fitted_model)
    if command.subcommand == "endogenous":
      cf_regression = self.state.cf_regression
      if cf_regression is not None:
        return _estat_cf_endogenous_table(cf_regression)
      iv_regression = self.state.iv_regression
      if iv_regression is None:
        raise ExecutionError("estat endogenous requires a prior cfregress model")
      if iv_regression.estimator != "2sls":
        raise ExecutionError("estat endogenous requires a prior ivregress 2sls model")
      return _estat_iv_endogenous_table(iv_regression.fitted_model)
    if command.subcommand == "margins":
      binary_regression = self.state.binary_regression
      if binary_regression is None:
        raise ExecutionError("estat margins requires a prior logit or probit model")
      return _estat_binary_margins_table(
        binary_regression.fitted_model,
        predictor_names=binary_regression.predictor_names,
      )
    if command.subcommand == "gof":
      poisson_regression = self.state.poisson_regression
      if poisson_regression is not None:
        return _estat_poisson_gof_table(poisson_regression.fitted_model)
      nbreg_regression = self.state.nbreg_regression
      if nbreg_regression is not None:
        return _estat_nbreg_gof_table(nbreg_regression.fitted_model)
      zip_regression = self.state.zip_regression
      if zip_regression is not None:
        return _estat_zip_gof_table(zip_regression.fitted_model)
      zinb_regression = self.state.zinb_regression
      if zinb_regression is not None:
        return _estat_zinb_gof_table(zinb_regression.fitted_model)
      raise ExecutionError("estat gof requires a prior poisson, nbreg, zip, or zinb model")
    if command.subcommand == "did":
      did_regression = self.state.did_regression
      if did_regression is None:
        raise ExecutionError("estat did requires a prior did model")
      return _estat_did_table(did_regression.fitted_model)
    raise ExecutionError(f"estat unsupported subcommand: {command.subcommand}")

  def _execute_xtreg(self, command: XtRegCommand) -> XtRegressionResult:
    dataset = self._require_active_dataset("xtreg")
    panel_metadata = dataset.panel_metadata
    if panel_metadata is None:
      raise ExecutionError("xtreg requires panel metadata; run panel <id_var> <time_var> first")
    variables: tuple[str, ...] = (
      panel_metadata.id_variable,
      panel_metadata.time_variable,
      command.outcome,
      *command.predictors,
    )
    if command.cluster_variable is not None:
      variables = (*variables, command.cluster_variable)
    column_types = {column.name: column.data_type for column in dataset.columns}
    missing = tuple(variable for variable in variables if variable not in column_types)
    if missing:
      raise UnknownVariableError(f"xtreg unknown variable: {', '.join(missing)}")
    _require_numeric_columns("xtreg", dataset, (command.outcome, *command.predictors))
    rows = self.backend.regression_rows(dataset, variables)
    panel = _xt_panel_sample(
      rows=rows,
      predictor_count=len(command.predictors),
      has_cluster=command.cluster_variable is not None,
    )
    if panel is None:
      raise ExecutionError("xtreg requires at least one complete observation")
    outcome, exogenous, entity_ids, time_ids, cluster_values = panel
    sample_fingerprint = _xt_sample_fingerprint(
      outcomes=outcome,
      predictors=exogenous,
      entity_ids=entity_ids,
      time_ids=time_ids,
    )
    frame_data: dict[str, object] = {
      panel_metadata.id_variable: entity_ids,
      panel_metadata.time_variable: time_ids,
      command.outcome: outcome,
    }
    for index, predictor in enumerate(command.predictors):
      frame_data[predictor] = tuple(row[index] for row in exogenous)
    model_frame = _data_frame(frame_data, panel_metadata.id_variable, panel_metadata.time_variable)
    outcome_series = model_frame[command.outcome]
    predictor_frame = model_frame[list(command.predictors)]
    cov_type = "unadjusted"
    cov_label = "nonrobust"
    fit_kwargs: dict[str, Any] = {}
    if command.robust:
      cov_type = "robust"
      cov_label = "robust"
    if command.cluster_variable is not None:
      cov_type = "clustered"
      cov_label = f"cluster({command.cluster_variable})"
      if cluster_values is None:
        raise ExecutionError("xtreg requires complete cluster values")
      cluster_frame_data: dict[str, object] = {
        panel_metadata.id_variable: entity_ids,
        panel_metadata.time_variable: time_ids,
        command.cluster_variable: cluster_values,
      }
      cluster_frame = _data_frame(
        cluster_frame_data,
        panel_metadata.id_variable,
        panel_metadata.time_variable,
      )
      fit_kwargs["clusters"] = cluster_frame[[command.cluster_variable]]
    fitted: Any
    try:
      if command.estimator == "fe":
        fitted = PanelOLS(outcome_series, predictor_frame, entity_effects=True).fit(
          cov_type=cov_type,
          **fit_kwargs,
        )
      else:
        fitted = RandomEffects(outcome_series, predictor_frame).fit(
          cov_type=cov_type,
          **fit_kwargs,
        )
    except Exception as exc:
      raise ExecutionError("xtreg failed") from exc
    coefficients = _panel_coefficient_estimates(command.predictors, fitted)
    state = _XtRegressionState(
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      panel_metadata=panel_metadata,
      estimator=command.estimator,
      covariance=cov_label,
      cluster_variable=command.cluster_variable,
      sample_fingerprint=sample_fingerprint,
      fitted_model=fitted,
    )
    if command.estimator == "fe":
      self.state.xt_regressions.fe = state
    else:
      self.state.xt_regressions.re = state
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.did_regression = None
    return XtRegressionResult(
      estimator=command.estimator,
      covariance=cov_label,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(outcome),
      r_squared_within=_to_float(getattr(fitted, "rsquared_within", None)),
      r_squared_between=_to_float(getattr(fitted, "rsquared_between", None)),
      r_squared_overall=_to_float(getattr(fitted, "rsquared_overall", None)),
      coefficients=coefficients,
    )

  def _execute_xtdata(self, command: XtDataCommand) -> TransformResult:
    dataset = self._require_active_dataset("xtdata")
    panel_metadata = dataset.panel_metadata
    if panel_metadata is None:
      raise ExecutionError("xtdata requires panel metadata; run panel <id_var> <time_var> first")
    _require_numeric_columns("xtdata", dataset, command.variables)
    column_names = {column.name for column in dataset.columns}
    suffix = f"_{command.transform}"
    collisions = tuple(
      target
      for target in (f"{variable}{suffix}" for variable in command.variables)
      if target in column_names
    )
    if collisions:
      raise ExecutionError(f"xtdata target already exists: {', '.join(collisions)}")
    next_dataset = self.backend.xtdata_transform(
      dataset,
      command.variables,
      panel_id_variable=panel_metadata.id_variable,
      transform=command.transform,
    )
    next_dataset = _preserve_panel_metadata(dataset, next_dataset)
    return self._record_transform(f"Applied xtdata {command.transform} transform", next_dataset)

  def _execute_xtabond(self, command: XtAbondCommand) -> XtAbondRegressionResult:
    dataset = self._require_active_dataset("xtabond")
    panel_metadata = dataset.panel_metadata
    if panel_metadata is None:
      raise ExecutionError("xtabond requires panel metadata; run panel <id_var> <time_var> first")
    variables: tuple[str, ...] = (
      panel_metadata.id_variable,
      panel_metadata.time_variable,
      command.outcome,
      *command.predictors,
    )
    column_types = {column.name: column.data_type for column in dataset.columns}
    missing = tuple(variable for variable in variables if variable not in column_types)
    if missing:
      raise UnknownVariableError(f"xtabond unknown variable: {', '.join(missing)}")
    _require_numeric_columns("xtabond", dataset, (command.outcome, *command.predictors))
    rows = self.backend.regression_rows(dataset, variables)
    sample = _xtabond_sample(
      rows=rows,
      predictor_count=len(command.predictors),
    )
    if sample is None:
      raise ExecutionError("xtabond requires at least one complete observation")
    dependent, exogenous, endogenous, instruments = sample
    covariance_label = "robust" if command.robust else "nonrobust"
    cov_type: Literal["robust", "unadjusted"] = "robust" if command.robust else "unadjusted"
    try:
      fit = _fit_xtabond_python(
        dependent=dependent,
        exogenous=exogenous,
        endogenous=endogenous,
        instruments=instruments,
        outcome_name=command.outcome,
        predictor_names=command.predictors,
        cov_type=cov_type,
      )
    except ExecutionError:
      fit = _fit_xtabond_r_fallback(
        rows=rows,
        predictor_count=len(command.predictors),
        panel_id_name=panel_metadata.id_variable,
        panel_time_name=panel_metadata.time_variable,
        outcome_name=command.outcome,
        predictor_names=command.predictors,
        cov_label=covariance_label,
      )
    coefficients = fit.coefficients
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = None
    return XtAbondRegressionResult(
      covariance=fit.covariance,
      outcome=command.outcome,
      predictors=command.predictors,
      observation_count=len(dependent),
      coefficient_count=len(coefficients),
      coefficients=coefficients,
    )

  def _execute_did(self, command: DidCommand) -> DidRegressionResult:
    dataset = self._require_active_dataset("did")
    panel_metadata = dataset.panel_metadata
    if panel_metadata is None:
      raise ExecutionError("did requires panel metadata; run panel <id_var> <time_var> first")
    variables: tuple[str, ...] = (
      panel_metadata.id_variable,
      panel_metadata.time_variable,
      command.outcome,
      *command.controls,
      command.treatment_variable,
      command.post_variable,
    )
    column_types = {column.name: column.data_type for column in dataset.columns}
    missing = tuple(variable for variable in variables if variable not in column_types)
    if missing:
      raise UnknownVariableError(f"did unknown variable: {', '.join(missing)}")
    _require_numeric_columns(
      "did",
      dataset,
      (command.outcome, *command.controls, command.treatment_variable, command.post_variable),
    )
    rows = self.backend.regression_rows(dataset, variables)
    panel = _xt_panel_sample(
      rows=rows,
      predictor_count=len(command.controls) + 2,
      has_cluster=False,
    )
    if panel is None:
      raise ExecutionError("did requires at least one complete observation")
    outcomes, predictors, entity_ids, time_ids, _ = panel
    treatment_index = len(command.controls)
    post_index = treatment_index + 1
    treatment_values = tuple(row[treatment_index] for row in predictors)
    post_values = tuple(row[post_index] for row in predictors)
    allowed = {0.0, 1.0}
    if set(treatment_values) - allowed or set(post_values) - allowed:
      raise ExecutionError("did treatment and post variables must be binary with values 0 and 1")
    frame_data: dict[str, object] = {
      panel_metadata.id_variable: entity_ids,
      panel_metadata.time_variable: time_ids,
      command.outcome: outcomes,
    }
    for index, control in enumerate(command.controls):
      frame_data[control] = tuple(row[index] for row in predictors)
    interaction_name = "__tabdat_did_interaction"
    frame_data[interaction_name] = tuple(
      treat * post for treat, post in zip(treatment_values, post_values, strict=True)
    )
    model_frame = _data_frame(frame_data, panel_metadata.id_variable, panel_metadata.time_variable)
    outcome_series = model_frame[command.outcome]
    predictor_names = [*command.controls, interaction_name]
    predictor_frame = model_frame[predictor_names]
    cov_type = "robust" if command.robust else "unadjusted"
    covariance_label = "robust" if command.robust else "nonrobust"
    try:
      fitted = PanelOLS(
        outcome_series,
        predictor_frame,
        entity_effects=True,
        time_effects=True,
      ).fit(cov_type=cov_type)
    except Exception as exc:
      raise ExecutionError("did failed") from exc
    fitted_names = (*command.controls, interaction_name)
    raw_coefficients = _panel_coefficient_estimates(fitted_names, fitted)
    coefficients = tuple(
      CoefficientEstimate(
        name="did_interaction" if estimate.name == interaction_name else estimate.name,
        value=estimate.value,
        standard_error=estimate.standard_error,
        statistic=estimate.statistic,
        p_value=estimate.p_value,
      )
      for estimate in raw_coefficients
    )
    self.state.regression = None
    self.state.qreg_regression = None
    self.state.binary_regression = None
    self.state.nl_regression = None
    self.state.poisson_regression = None
    self.state.nbreg_regression = None
    self.state.zip_regression = None
    self.state.zinb_regression = None
    self.state.streg_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
    self.state.did_regression = _DidRegressionState(
      outcome_variable=command.outcome,
      control_names=command.controls,
      treatment_variable=command.treatment_variable,
      post_variable=command.post_variable,
      fitted_model=fitted,
    )
    return DidRegressionResult(
      covariance=covariance_label,
      outcome=command.outcome,
      controls=command.controls,
      treatment_variable=command.treatment_variable,
      post_variable=command.post_variable,
      observation_count=len(outcomes),
      coefficients=coefficients,
    )

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
        EstatCommand,
      ),
    ):
      return
    dataset = self._require_active_dataset("materialize")
    materialized = self.backend.materialize_polars_lazy(dataset.path)
    materialized = replace(materialized, panel_metadata=dataset.panel_metadata)
    self.state.active_dataset = materialized


def _estat_residuals_table(fitted_model: object) -> TableResult:
  residuals = _required_float_sequence(getattr(fitted_model, "resid", None))
  if not residuals:
    raise ExecutionError("estat residuals failed for current model")
  rows: list[tuple[object, ...]] = [
    ("count", len(residuals)),
    ("mean", _mean(residuals)),
    ("std_dev", _sample_standard_deviation(residuals)),
    ("min", min(residuals)),
    ("median", _median(residuals)),
    ("max", max(residuals)),
  ]
  studentized = _studentized_residuals(fitted_model)
  if studentized is not None:
    rows.append(("studentized_std_dev", _sample_standard_deviation(studentized)))
  return TableResult(headers=("Metric", "Value"), rows=tuple(rows))


def _estat_did_table(fitted_model: object) -> TableResult:
  params = getattr(fitted_model, "params", None)
  names = tuple(str(name) for name in getattr(params, "index", ()))
  coefficients = _required_float_sequence(params)
  if len(names) != len(coefficients):
    raise ExecutionError("estat did failed for current model")
  target_name = "__tabdat_did_interaction"
  if target_name not in names:
    raise ExecutionError("estat did failed for current model")
  index = names.index(target_name)
  std_errors = _optional_float_sequence(getattr(fitted_model, "std_errors", None))
  statistics = _optional_float_sequence(getattr(fitted_model, "tstats", None))
  p_values = _optional_float_sequence(getattr(fitted_model, "pvalues", None))
  rows: tuple[tuple[object, ...], ...] = (
    ("did_interaction", "coefficient", coefficients[index]),
    ("did_interaction", "std_error", _optional_sequence_value(std_errors, index)),
    ("did_interaction", "statistic", _optional_sequence_value(statistics, index)),
    ("did_interaction", "p_value", _optional_sequence_value(p_values, index)),
    ("did_interaction", "observation_count", _to_float(getattr(fitted_model, "nobs", None))),
  )
  return TableResult(headers=("Test", "Metric", "Value"), rows=rows)


def _estat_ovtest_table(fitted_model: object) -> TableResult:
  try:
    reset_result = linear_reset(cast(Any, fitted_model), use_f=True)
  except Exception as exc:
    raise ExecutionError("estat ovtest failed for current model") from exc
  return TableResult(
    headers=("Metric", "Value"),
    rows=(
      ("F", _to_float(getattr(reset_result, "fvalue", None))),
      ("p_value", _to_float(getattr(reset_result, "pvalue", None))),
      ("df_num", _to_float(getattr(reset_result, "df_num", None))),
      ("df_denom", _to_float(getattr(reset_result, "df_denom", None))),
    ),
  )


def _estat_vif_table(
  fitted_model: object,
  *,
  predictor_names: tuple[str, ...],
  include_intercept: bool,
) -> TableResult:
  exog = getattr(getattr(fitted_model, "model", None), "exog", None)
  column_count = _matrix_column_count(exog)
  index_offset = 1 if include_intercept else 0
  if column_count is None or column_count < len(predictor_names) + index_offset:
    raise ExecutionError("estat vif failed for current model")
  rows: list[tuple[object, ...]] = []
  vif_values: list[float] = []
  for column_index, predictor in enumerate(predictor_names, start=index_offset):
    try:
      vif = _to_float_allow_inf(variance_inflation_factor(exog, column_index))
    except Exception as exc:
      raise ExecutionError("estat vif failed for current model") from exc
    rows.append((predictor, vif))
    if vif is not None:
      vif_values.append(vif)
  if not rows:
    raise ExecutionError("estat vif failed for current model")
  if vif_values:
    rows.append(("mean_vif", _mean(tuple(vif_values))))
  return TableResult(headers=("Variable", "VIF"), rows=tuple(rows))


def _estat_iv_firststage_table(fitted_model: object) -> TableResult:
  diagnostics = getattr(getattr(fitted_model, "first_stage", None), "diagnostics", None)
  if diagnostics is None:
    raise ExecutionError("estat firststage failed for current model")
  try:
    index_names = tuple(getattr(diagnostics, "index"))
  except Exception as exc:
    raise ExecutionError("estat firststage failed for current model") from exc
  rows: list[tuple[object, ...]] = []
  for variable in index_names:
    values = {
      "rsquared": _to_float(diagnostics.loc[variable, "rsquared"]),
      "partial.rsquared": _to_float(diagnostics.loc[variable, "partial.rsquared"]),
      "shea.rsquared": _to_float(diagnostics.loc[variable, "shea.rsquared"]),
      "f.stat": _to_float(diagnostics.loc[variable, "f.stat"]),
      "f.pval": _to_float(diagnostics.loc[variable, "f.pval"]),
      "f.dist": str(diagnostics.loc[variable, "f.dist"]),
    }
    rows.extend(
      (
        (str(variable), "r_squared", values["rsquared"]),
        (str(variable), "partial_r_squared", values["partial.rsquared"]),
        (str(variable), "shea_r_squared", values["shea.rsquared"]),
        (str(variable), "partial_f", values["f.stat"]),
        (str(variable), "p_value", values["f.pval"]),
        (str(variable), "distribution", values["f.dist"]),
      )
    )
  if not rows:
    raise ExecutionError("estat firststage failed for current model")
  return TableResult(headers=("Variable", "Metric", "Value"), rows=tuple(rows))


def _estat_iv_overid_table(fitted_model: object) -> TableResult:
  gmm_j_test = getattr(fitted_model, "j_stat", None)
  if gmm_j_test is not None:
    return _iv_test_table_rows((("gmm_j", gmm_j_test),))

  tests = (
    ("sargan", getattr(fitted_model, "sargan", None)),
    ("wooldridge_overid", getattr(fitted_model, "wooldridge_overid", None)),
  )
  return _iv_test_table_rows(tests)


def _iv_test_table_rows(
  tests: tuple[tuple[str, object | None], ...],
) -> TableResult:
  rows: list[tuple[object, ...]] = []
  for name, test in tests:
    if test is None:
      rows.extend(
        (
          (name, "statistic", None),
          (name, "p_value", None),
          (name, "df", None),
          (name, "distribution", "not_available"),
        )
      )
      continue
    dist_name = str(getattr(test, "dist_name", "")).strip()
    rows.extend(
      (
        (name, "statistic", _to_float(getattr(test, "stat", None))),
        (name, "p_value", _to_float(getattr(test, "pval", None))),
        (name, "df", _to_float(getattr(test, "df", None))),
        (name, "distribution", dist_name if dist_name and dist_name != "None" else "not_available"),
      )
    )
  if not rows:
    raise ExecutionError("estat overid failed for current model")
  return TableResult(headers=("Test", "Metric", "Value"), rows=tuple(rows))


def _estat_iv_endogenous_table(fitted_model: object) -> TableResult:
  tests = (
    ("durbin", _invoke_iv_test_stat(fitted_model, "durbin")),
    ("wu_hausman", _invoke_iv_test_stat(fitted_model, "wu_hausman")),
  )
  rows: list[tuple[object, ...]] = []
  for name, test in tests:
    if test is None:
      raise ExecutionError("estat endogenous failed for current model")
    dist_name = str(getattr(test, "dist_name", "")).strip()
    rows.extend(
      (
        (name, "statistic", _to_float(getattr(test, "stat", None))),
        (name, "p_value", _to_float(getattr(test, "pval", None))),
        (name, "df", _to_float(getattr(test, "df", None))),
        (name, "distribution", dist_name if dist_name and dist_name != "None" else "not_available"),
      )
    )
  return TableResult(headers=("Test", "Metric", "Value"), rows=tuple(rows))


def _estat_binary_margins_table(
  fitted_model: object,
  *,
  predictor_names: tuple[str, ...],
) -> TableResult:
  try:
    margins = cast(Any, fitted_model).get_margeff(at="overall")
    summary = margins.summary_frame()
    raw_index = getattr(summary, "index", ())
    index: tuple[object, ...] = tuple(raw_index)
  except Exception as exc:
    raise ExecutionError("estat margins failed for current model") from exc
  if not index:
    raise ExecutionError("estat margins failed for current model")
  margin_variables = (
    predictor_names if len(predictor_names) == len(index) else tuple(str(name) for name in index)
  )
  rows: list[tuple[object, ...]] = []
  for variable, summary_name in zip(margin_variables, index, strict=True):
    try:
      effect = _to_float(summary.loc[summary_name, "dy/dx"])
      std_error = _to_float(summary.loc[summary_name, "Std. Err."])
      statistic = _to_float(summary.loc[summary_name, "z"])
      p_value = _to_float(summary.loc[summary_name, "Pr(>|z|)"])
      ci_lower = _to_float(summary.loc[summary_name, "Conf. Int. Low"])
      ci_upper = _to_float(summary.loc[summary_name, "Cont. Int. Hi."])
    except Exception as exc:
      raise ExecutionError("estat margins failed for current model") from exc
    rows.extend(
      (
        (str(variable), "dy_dx", effect),
        (str(variable), "std_error", std_error),
        (str(variable), "statistic", statistic),
        (str(variable), "p_value", p_value),
        (str(variable), "ci_lower", ci_lower),
        (str(variable), "ci_upper", ci_upper),
      )
    )
  return TableResult(headers=("Variable", "Metric", "Value"), rows=tuple(rows))


def _estat_poisson_gof_table(fitted_model: object) -> TableResult:
  try:
    llf = _to_float(getattr(fitted_model, "llf", None))
    llnull = _to_float(getattr(fitted_model, "llnull", None))
    if llf is not None and llnull is not None and llnull != 0:
      pseudo_r2 = 1.0 - (llf / llnull)
    else:
      pseudo_r2 = None
    resid_pearson = np.array(getattr(fitted_model, "resid_pearson", ()), dtype=float)
    resid_deviance = np.array(getattr(fitted_model, "resid_deviance", ()), dtype=float)
  except Exception as exc:
    raise ExecutionError("estat gof failed for current model") from exc
  if resid_pearson.ndim != 1 or resid_deviance.ndim != 1:
    raise ExecutionError("estat gof failed for current model")
  pearson_chi2 = float(np.dot(resid_pearson, resid_pearson)) if resid_pearson.size > 0 else None
  deviance = float(np.dot(resid_deviance, resid_deviance)) if resid_deviance.size > 0 else None
  rows = (
    ("log_likelihood", llf),
    ("log_likelihood_null", llnull),
    ("pseudo_r_squared", pseudo_r2),
    ("pearson_chi2", pearson_chi2),
    ("deviance", deviance),
    ("observation_count", _to_float(getattr(fitted_model, "nobs", None))),
  )
  return TableResult(headers=("Metric", "Value"), rows=rows)


def _estat_nbreg_gof_table(fitted_model: object) -> TableResult:
  try:
    llf = _to_float(getattr(fitted_model, "llf", None))
    llnull = _to_float(getattr(fitted_model, "llnull", None))
    if llf is not None and llnull is not None and llnull != 0:
      pseudo_r2 = 1.0 - (llf / llnull)
    else:
      pseudo_r2 = None
    resid_pearson = np.array(getattr(fitted_model, "resid_pearson", ()), dtype=float)
  except Exception as exc:
    raise ExecutionError("estat gof failed for current model") from exc
  if resid_pearson.ndim != 1:
    raise ExecutionError("estat gof failed for current model")
  pearson_chi2 = float(np.dot(resid_pearson, resid_pearson)) if resid_pearson.size > 0 else None
  rows = (
    ("log_likelihood", llf),
    ("log_likelihood_null", llnull),
    ("pseudo_r_squared", pseudo_r2),
    ("pearson_chi2", pearson_chi2),
    ("aic", _to_float(getattr(fitted_model, "aic", None))),
    ("bic", _to_float(getattr(fitted_model, "bic", None))),
    ("lnalpha", _to_float(getattr(fitted_model, "lnalpha", None))),
    ("lnalpha_std_err", _to_float(getattr(fitted_model, "lnalpha_std_err", None))),
    ("observation_count", _to_float(getattr(fitted_model, "nobs", None))),
  )
  return TableResult(headers=("Metric", "Value"), rows=rows)


def _estat_zip_gof_table(fitted_model: object) -> TableResult:
  try:
    llf = _to_float(getattr(fitted_model, "llf", None))
    llnull = _to_float(getattr(fitted_model, "llnull", None))
    if llf is not None and llnull is not None and llnull != 0:
      pseudo_r2 = 1.0 - (llf / llnull)
    else:
      pseudo_r2 = None
    resid_pearson = np.array(getattr(fitted_model, "resid_pearson", ()), dtype=float)
  except Exception as exc:
    raise ExecutionError("estat gof failed for current model") from exc
  if resid_pearson.ndim != 1:
    raise ExecutionError("estat gof failed for current model")
  pearson_chi2 = float(np.dot(resid_pearson, resid_pearson)) if resid_pearson.size > 0 else None
  rows = (
    ("log_likelihood", llf),
    ("log_likelihood_null", llnull),
    ("pseudo_r_squared", pseudo_r2),
    ("pearson_chi2", pearson_chi2),
    ("aic", _to_float(getattr(fitted_model, "aic", None))),
    ("bic", _to_float(getattr(fitted_model, "bic", None))),
    ("observation_count", _to_float(getattr(fitted_model, "nobs", None))),
  )
  return TableResult(headers=("Metric", "Value"), rows=rows)


def _estat_zinb_gof_table(fitted_model: object) -> TableResult:
  try:
    llf = _to_float(getattr(fitted_model, "llf", None))
    llnull = _to_float(getattr(fitted_model, "llnull", None))
    if llf is not None and llnull is not None and llnull != 0:
      pseudo_r2 = 1.0 - (llf / llnull)
    else:
      pseudo_r2 = None
    resid_pearson = np.array(getattr(fitted_model, "resid_pearson", ()), dtype=float)
  except Exception as exc:
    raise ExecutionError("estat gof failed for current model") from exc
  if resid_pearson.ndim != 1:
    raise ExecutionError("estat gof failed for current model")
  pearson_chi2 = float(np.dot(resid_pearson, resid_pearson)) if resid_pearson.size > 0 else None
  rows = (
    ("log_likelihood", llf),
    ("log_likelihood_null", llnull),
    ("pseudo_r_squared", pseudo_r2),
    ("pearson_chi2", pearson_chi2),
    ("aic", _to_float(getattr(fitted_model, "aic", None))),
    ("bic", _to_float(getattr(fitted_model, "bic", None))),
    ("lnalpha", _to_float(getattr(fitted_model, "lnalpha", None))),
    ("observation_count", _to_float(getattr(fitted_model, "nobs", None))),
  )
  return TableResult(headers=("Metric", "Value"), rows=rows)


def _invoke_iv_test_stat(fitted_model: object, attribute_name: str) -> object | None:
  test_method = getattr(fitted_model, attribute_name, None)
  if not callable(test_method):
    return None
  try:
    return cast(object, test_method())
  except Exception:
    return None


def _estat_hausman_table(fe_model: object, re_model: object) -> TableResult:
  fe_params = _parameter_vector(getattr(fe_model, "params", None), "xtreg")
  re_params = _parameter_vector(getattr(re_model, "params", None), "xtreg")
  fe_covariance = _covariance_matrix(getattr(fe_model, "cov", None), "xtreg")
  re_covariance = _covariance_matrix(getattr(re_model, "cov", None), "xtreg")
  if fe_params.shape != re_params.shape or fe_covariance.shape != re_covariance.shape:
    raise ExecutionError("estat hausman failed for current models")
  delta = fe_params - re_params
  cov_difference = fe_covariance - re_covariance
  try:
    inverse_cov = np.linalg.pinv(cov_difference)
    statistic = float(delta.T @ inverse_cov @ delta)
  except Exception as exc:
    raise ExecutionError("estat hausman failed for current models") from exc
  statistic = max(statistic, 0.0)
  degrees_of_freedom = int(delta.shape[0])
  if degrees_of_freedom <= 0:
    raise ExecutionError("estat hausman failed for current models")
  p_value = float(chi2.sf(statistic, degrees_of_freedom))
  return TableResult(
    headers=("Metric", "Value"),
    rows=(
      ("chi2", statistic),
      ("p_value", p_value),
      ("df", degrees_of_freedom),
    ),
  )


def _estat_cf_endogenous_table(cf_regression: _CfRegressionState) -> TableResult:
  if (
    cf_regression.residual_estimate is None
    or cf_regression.residual_standard_error is None
    or cf_regression.residual_statistic is None
    or cf_regression.residual_p_value is None
    or cf_regression.residual_ci_level is None
    or cf_regression.residual_ci_lower is None
    or cf_regression.residual_ci_upper is None
    or cf_regression.residual_distribution is None
  ):
    raise ExecutionError("estat endogenous failed for current model")
  distribution_df = (
    cf_regression.residual_df if cf_regression.residual_df is not None else "not_available"
  )
  rows = (
    ("control_function_residual", "test", "cf_residual"),
    ("control_function_residual", "estimate", cf_regression.residual_estimate),
    ("control_function_residual", "std_error", cf_regression.residual_standard_error),
    ("control_function_residual", "statistic", cf_regression.residual_statistic),
    ("control_function_residual", "p_value", cf_regression.residual_p_value),
    ("control_function_residual", "ci_level", cf_regression.residual_ci_level),
    ("control_function_residual", "ci_lower", cf_regression.residual_ci_lower),
    ("control_function_residual", "ci_upper", cf_regression.residual_ci_upper),
    ("control_function_residual", "distribution", cf_regression.residual_distribution),
    ("control_function_residual", "df", distribution_df),
  )
  return TableResult(headers=("Test", "Metric", "Value"), rows=rows)


def _estat_cf_firststage_table(cf_regression: _CfRegressionState) -> TableResult:
  rows: list[tuple[object, ...]] = []
  for estimate in cf_regression.first_stage_coefficients:
    rows.extend(
      (
        (estimate.name, "coefficient", estimate.value),
        (estimate.name, "std_error", estimate.standard_error),
        (estimate.name, "statistic", estimate.statistic),
        (estimate.name, "p_value", estimate.p_value),
      )
    )
  rows.extend(
    (
      ("first_stage", "observation_count", cf_regression.first_stage_observation_count),
      ("first_stage", "r_squared", cf_regression.first_stage_r_squared),
    )
  )
  return TableResult(headers=("Variable", "Metric", "Value"), rows=tuple(rows))


def _cf_residual_diagnostic(
  *,
  coefficients: tuple[CoefficientEstimate, ...],
  include_intercept: bool,
  residual_index: int,
) -> tuple[float | None, float | None, float | None, float | None]:
  coefficient_index = residual_index + (1 if include_intercept else 0)
  if coefficient_index < 0 or coefficient_index >= len(coefficients):
    return (None, None, None, None)
  residual_coefficient = coefficients[coefficient_index]
  return (
    residual_coefficient.value,
    residual_coefficient.standard_error,
    residual_coefficient.statistic,
    residual_coefficient.p_value,
  )


def _cf_residual_confidence_interval(
  *,
  fitted_model: object,
  include_intercept: bool,
  residual_index: int,
) -> tuple[float | None, float | None, str | None, float | None]:
  coefficient_index = residual_index + (1 if include_intercept else 0)
  if coefficient_index < 0:
    return (None, None, None, None)
  try:
    confidence_intervals = np.asarray(getattr(fitted_model, "conf_int")(), dtype=float)
  except Exception:
    return (None, None, None, None)
  if confidence_intervals.ndim != 2 or confidence_intervals.shape[1] < 2:
    return (None, None, None, None)
  if coefficient_index >= confidence_intervals.shape[0]:
    return (None, None, None, None)
  lower = float(confidence_intervals[coefficient_index, 0])
  upper = float(confidence_intervals[coefficient_index, 1])
  use_t = bool(getattr(fitted_model, "use_t", False))
  distribution = "t" if use_t else "normal"
  degrees_of_freedom = _to_float(getattr(fitted_model, "df_resid", None)) if use_t else None
  return (lower, upper, distribution, degrees_of_freedom)


def _studentized_residuals(fitted_model: object) -> tuple[float, ...] | None:
  try:
    influence = OLSInfluence(cast(Any, fitted_model))
    return _required_float_sequence(getattr(influence, "resid_studentized_internal", None))
  except Exception:
    return None


def _matrix_column_count(matrix: object) -> int | None:
  if matrix is None:
    return None
  shape = getattr(matrix, "shape", None)
  if isinstance(shape, tuple) and len(shape) == 2 and isinstance(shape[1], int):
    return shape[1]
  return None


def _mean(values: tuple[float, ...]) -> float:
  return math.fsum(values) / len(values)


def _sample_standard_deviation(values: tuple[float, ...]) -> float | None:
  if len(values) < 2:
    return None
  mean_value = _mean(values)
  variance = math.fsum((value - mean_value) * (value - mean_value) for value in values) / (
    len(values) - 1
  )
  return math.sqrt(variance)


def _median(values: tuple[float, ...]) -> float:
  sorted_values = sorted(values)
  midpoint = len(sorted_values) // 2
  if len(sorted_values) % 2 == 1:
    return sorted_values[midpoint]
  return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2.0


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


def _logit_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
  has_cluster: bool,
) -> tuple[tuple[float, ...], tuple[tuple[float, ...], ...], tuple[object, ...] | None, bool]:
  outcomes: list[float] = []
  predictors: list[tuple[float, ...]] = []
  groups: list[object] = []
  missing_cluster_detected = False
  row_width = predictor_count + 1 + (1 if has_cluster else 0)
  for row in rows:
    if len(row) != row_width:
      continue
    raw_outcome = row[0]
    raw_predictors = row[1 : 1 + predictor_count]
    raw_group = row[-1] if has_cluster else None
    if raw_outcome is None or any(value is None for value in raw_predictors):
      continue
    outcome = _coerce_float(raw_outcome)
    predictor_values = tuple(
      value
      for value in (_coerce_float(raw_value) for raw_value in raw_predictors)
      if value is not None
    )
    if outcome is None or len(predictor_values) != predictor_count:
      continue
    if not math.isfinite(outcome) or any(not math.isfinite(value) for value in predictor_values):
      continue
    if has_cluster and raw_group is None:
      missing_cluster_detected = True
      continue
    outcomes.append(outcome)
    predictors.append(predictor_values)
    if has_cluster:
      groups.append(raw_group)
  group_values: tuple[object, ...] | None = tuple(groups) if has_cluster else None
  return tuple(outcomes), tuple(predictors), group_values, missing_cluster_detected


def _streg_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
  has_cluster: bool,
) -> tuple[
  tuple[float, ...],
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[object, ...] | None,
  bool,
]:
  times: list[float] = []
  failures: list[float] = []
  predictors: list[tuple[float, ...]] = []
  groups: list[object] = []
  missing_cluster_detected = False
  row_width = 2 + predictor_count + (1 if has_cluster else 0)
  for row in rows:
    if len(row) != row_width:
      continue
    raw_time = row[0]
    raw_failure = row[1]
    raw_predictors = row[2 : 2 + predictor_count]
    raw_group = row[-1] if has_cluster else None
    if raw_time is None or raw_failure is None or any(value is None for value in raw_predictors):
      continue
    time_value = _coerce_float(raw_time)
    failure_value = _coerce_float(raw_failure)
    predictor_values = tuple(
      value
      for value in (_coerce_float(raw_value) for raw_value in raw_predictors)
      if value is not None
    )
    if time_value is None or failure_value is None or len(predictor_values) != predictor_count:
      continue
    if not math.isfinite(time_value) or not math.isfinite(failure_value):
      continue
    if any(not math.isfinite(value) for value in predictor_values):
      continue
    if has_cluster and raw_group is None:
      missing_cluster_detected = True
      continue
    times.append(time_value)
    failures.append(failure_value)
    predictors.append(predictor_values)
    if has_cluster:
      groups.append(raw_group)
  group_values: tuple[object, ...] | None = tuple(groups) if has_cluster else None
  return tuple(times), tuple(failures), tuple(predictors), group_values, missing_cluster_detected


def _iv_regression_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  exogenous_count: int,
  instrument_count: int,
  has_cluster: bool,
) -> tuple[
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[object, ...] | None,
]:
  outcomes: list[float] = []
  exogenous_values: list[tuple[float, ...]] = []
  endogenous_values: list[float] = []
  instrument_values: list[tuple[float, ...]] = []
  clusters: list[object] = []
  row_width = 1 + exogenous_count + 1 + instrument_count + (1 if has_cluster else 0)
  for row in rows:
    if len(row) != row_width:
      raise ExecutionError("ivregress failed")
    outcome_raw = row[0]
    exog_start = 1
    exog_end = exog_start + exogenous_count
    endog_index = exog_end
    iv_start = endog_index + 1
    iv_end = iv_start + instrument_count
    cluster_value = row[iv_end] if has_cluster else None

    if (
      outcome_raw is None
      or row[endog_index] is None
      or any(value is None for value in row[exog_start:exog_end])
      or any(value is None for value in row[iv_start:iv_end])
    ):
      continue
    if has_cluster and cluster_value is None:
      continue

    outcome = _coerce_float(outcome_raw)
    endogenous = _coerce_float(row[endog_index])
    exog = tuple(
      value
      for value in (_coerce_float(raw) for raw in row[exog_start:exog_end])
      if value is not None
    )
    instruments = tuple(
      value for value in (_coerce_float(raw) for raw in row[iv_start:iv_end]) if value is not None
    )
    if outcome is None or endogenous is None:
      continue
    if len(exog) != exogenous_count or len(instruments) != instrument_count:
      continue
    numeric_values = (outcome, endogenous, *exog, *instruments)
    if any(not math.isfinite(value) for value in numeric_values):
      continue

    outcomes.append(outcome)
    exogenous_values.append(exog)
    endogenous_values.append(endogenous)
    instrument_values.append(instruments)
    if has_cluster:
      clusters.append(cluster_value)

  return (
    tuple(outcomes),
    tuple(exogenous_values),
    tuple(endogenous_values),
    tuple(instrument_values),
    tuple(clusters) if has_cluster else None,
  )


def _heckman_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  outcome_predictor_count: int,
  selection_predictor_count: int,
  has_cluster: bool,
) -> tuple[
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[object, ...] | None,
  bool,
]:
  outcomes: list[float] = []
  outcome_predictors: list[tuple[float, ...]] = []
  selection_outcomes: list[float] = []
  selection_predictors: list[tuple[float, ...]] = []
  clusters: list[object] = []
  missing_cluster_detected = False
  row_width = (
    1 + outcome_predictor_count + 1 + selection_predictor_count + (1 if has_cluster else 0)
  )
  outcome_predictor_end = 1 + outcome_predictor_count
  selection_index = outcome_predictor_end
  selection_predictor_start = selection_index + 1
  selection_predictor_end = selection_predictor_start + selection_predictor_count
  for row in rows:
    if len(row) != row_width:
      continue
    cluster_value = row[selection_predictor_end] if has_cluster else None
    if (
      row[0] is None
      or row[selection_index] is None
      or any(value is None for value in row[1:outcome_predictor_end])
      or any(value is None for value in row[selection_predictor_start:selection_predictor_end])
    ):
      continue
    if has_cluster and cluster_value is None:
      missing_cluster_detected = True
      continue
    outcome_value = _coerce_float(row[0])
    selection_value = _coerce_float(row[selection_index])
    out_predictors = tuple(
      value
      for value in (_coerce_float(raw) for raw in row[1:outcome_predictor_end])
      if value is not None
    )
    sel_predictors = tuple(
      value
      for value in (
        _coerce_float(raw) for raw in row[selection_predictor_start:selection_predictor_end]
      )
      if value is not None
    )
    if outcome_value is None or selection_value is None:
      continue
    if (
      len(out_predictors) != outcome_predictor_count
      or len(sel_predictors) != selection_predictor_count
    ):
      continue
    if any(
      not math.isfinite(value)
      for value in (outcome_value, selection_value, *out_predictors, *sel_predictors)
    ):
      continue
    outcomes.append(outcome_value)
    outcome_predictors.append(out_predictors)
    selection_outcomes.append(selection_value)
    selection_predictors.append(sel_predictors)
    if has_cluster:
      clusters.append(cluster_value)
  return (
    tuple(outcomes),
    tuple(outcome_predictors),
    tuple(selection_outcomes),
    tuple(selection_predictors),
    tuple(clusters) if has_cluster else None,
    missing_cluster_detected,
  )


def _xt_panel_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
  has_cluster: bool,
) -> (
  tuple[
    tuple[float, ...],
    tuple[tuple[float, ...], ...],
    tuple[object, ...],
    tuple[object, ...],
    tuple[object, ...] | None,
  ]
  | None
):
  outcomes: list[float] = []
  predictors: list[tuple[float, ...]] = []
  entity_ids: list[object] = []
  time_ids: list[object] = []
  clusters: list[object] = []
  row_width = 2 + 1 + predictor_count + (1 if has_cluster else 0)
  for row in rows:
    if len(row) != row_width:
      raise ExecutionError("xtreg failed")
    entity_id = row[0]
    time_id = row[1]
    outcome_raw = row[2]
    predictor_start = 3
    predictor_end = predictor_start + predictor_count
    cluster_value = row[predictor_end] if has_cluster else None
    if entity_id is None or time_id is None or outcome_raw is None:
      continue
    if any(value is None for value in row[predictor_start:predictor_end]):
      continue
    if has_cluster and cluster_value is None:
      continue
    outcome = _coerce_float(outcome_raw)
    predictor_values = tuple(
      value
      for value in (_coerce_float(raw_value) for raw_value in row[predictor_start:predictor_end])
      if value is not None
    )
    if outcome is None or len(predictor_values) != predictor_count:
      continue
    if not math.isfinite(outcome) or any(not math.isfinite(value) for value in predictor_values):
      continue
    outcomes.append(outcome)
    predictors.append(predictor_values)
    entity_ids.append(entity_id)
    time_ids.append(time_id)
    if has_cluster:
      clusters.append(cluster_value)
  if not outcomes:
    return None
  return (
    tuple(outcomes),
    tuple(predictors),
    tuple(entity_ids),
    tuple(time_ids),
    tuple(clusters) if has_cluster else None,
  )


def _xt_sample_fingerprint(
  *,
  outcomes: tuple[float, ...],
  predictors: tuple[tuple[float, ...], ...],
  entity_ids: tuple[object, ...],
  time_ids: tuple[object, ...],
) -> str:
  digest = hashlib.sha256()
  for outcome, predictor_row, entity_id, time_id in zip(
    outcomes,
    predictors,
    entity_ids,
    time_ids,
    strict=True,
  ):
    digest.update(repr(entity_id).encode("utf-8"))
    digest.update(b"\x1f")
    digest.update(repr(time_id).encode("utf-8"))
    digest.update(b"\x1f")
    digest.update(f"{outcome:.17g}".encode())
    for predictor in predictor_row:
      digest.update(b"\x1f")
      digest.update(f"{predictor:.17g}".encode())
    digest.update(b"\x1e")
  return digest.hexdigest()


def _xtabond_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
) -> (
  tuple[
    tuple[float, ...],
    tuple[tuple[float, ...], ...] | None,
    tuple[float, ...],
    tuple[tuple[float, ...], ...],
  ]
  | None
):
  grouped: dict[object, list[tuple[object, float, tuple[float, ...]]]] = {}
  row_width = 3 + predictor_count
  for row in rows:
    if len(row) != row_width:
      raise ExecutionError("xtabond failed")
    entity_id = row[0]
    time_id = row[1]
    outcome = _coerce_float(row[2])
    predictor_values = tuple(
      value for value in (_coerce_float(raw) for raw in row[3:]) if value is not None
    )
    if entity_id is None or time_id is None or outcome is None:
      continue
    if len(predictor_values) != predictor_count:
      continue
    if not math.isfinite(outcome) or any(not math.isfinite(value) for value in predictor_values):
      continue
    grouped.setdefault(entity_id, []).append((time_id, outcome, predictor_values))

  dependent: list[float] = []
  exogenous: list[tuple[float, ...]] = []
  endogenous: list[float] = []
  instruments: list[tuple[float, ...]] = []
  for entity_rows in grouped.values():
    entity_rows.sort(key=lambda item: _xtabond_time_sort_key(item[0]))
    if len(entity_rows) < 3:
      continue
    for index in range(2, len(entity_rows)):
      _, outcome_t, predictors_t = entity_rows[index]
      _, outcome_t_minus_1, predictors_t_minus_1 = entity_rows[index - 1]
      _, outcome_t_minus_2, _ = entity_rows[index - 2]
      delta_outcome = outcome_t - outcome_t_minus_1
      delta_lag_outcome = outcome_t_minus_1 - outcome_t_minus_2
      delta_predictors = tuple(
        current - previous
        for current, previous in zip(predictors_t, predictors_t_minus_1, strict=True)
      )
      if any(
        not math.isfinite(value)
        for value in (delta_outcome, delta_lag_outcome, outcome_t_minus_2, *delta_predictors)
      ):
        continue
      dependent.append(delta_outcome)
      endogenous.append(delta_lag_outcome)
      exogenous.append(delta_predictors)
      instruments.append((outcome_t_minus_2,))
  if not dependent:
    return None
  return (
    tuple(dependent),
    tuple(exogenous) if predictor_count > 0 else None,
    tuple(endogenous),
    tuple(instruments),
  )


def _xtabond_time_sort_key(value: object) -> tuple[int, object]:
  numeric = _coerce_float(value)
  if numeric is not None and math.isfinite(numeric):
    return (0, numeric)
  return (1, repr(value))


def _fit_xtabond_python(
  *,
  dependent: tuple[float, ...],
  exogenous: tuple[tuple[float, ...], ...] | None,
  endogenous: tuple[float, ...],
  instruments: tuple[tuple[float, ...], ...],
  outcome_name: str,
  predictor_names: tuple[str, ...],
  cov_type: Literal["robust", "unadjusted"],
) -> _XtAbondFitResult:
  try:
    exog_data = np.array(exogenous, dtype=float) if exogenous is not None else None
    model = IVGMM(
      dependent=np.array(dependent, dtype=float),
      exog=exog_data,
      endog=np.array(endogenous, dtype=float),
      instruments=np.array(instruments, dtype=float),
    )
    fitted = model.fit(cov_type=cov_type)
  except Exception as exc:
    raise ExecutionError("xtabond failed") from exc
  parameter_names = (*predictor_names, f"L1.{outcome_name}")
  coefficients = _iv_coefficient_estimates(parameter_names, fitted)
  covariance = "robust" if cov_type == "robust" else "nonrobust"
  return _XtAbondFitResult(covariance=covariance, coefficients=coefficients)


def _fit_xtabond_r_fallback(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
  panel_id_name: str,
  panel_time_name: str,
  outcome_name: str,
  predictor_names: tuple[str, ...],
  cov_label: str,
) -> _XtAbondFitResult:
  try:
    from rpy2 import robjects
    from rpy2.robjects import packages
    from rpy2.robjects.vectors import FloatVector, StrVector
  except Exception as exc:
    raise ExecutionError("xtabond failed") from exc
  try:
    user_library = Path.home() / "R/library"
    if user_library.exists():
      libpaths_fn = cast(Any, robjects.r[".libPaths"])
      current_paths = tuple(str(path) for path in libpaths_fn())
      libpaths_fn(StrVector((str(user_library), *current_paths)))
    require_namespace = cast(Any, robjects.r["requireNamespace"])
    if not bool(require_namespace("plm", quietly=True)[0]):
      raise ExecutionError("xtabond failed")
    stats = packages.importr("stats")
    plm = packages.importr("plm")
    row_width = 3 + predictor_count
    id_values: list[str] = []
    time_values: list[str] = []
    outcome_values: list[float] = []
    predictor_values: dict[str, list[float]] = {name: [] for name in predictor_names}
    for row in rows:
      if len(row) != row_width:
        continue
      entity_id = row[0]
      time_id = row[1]
      outcome = _coerce_float(row[2])
      if entity_id is None or time_id is None or outcome is None or not math.isfinite(outcome):
        continue
      current_predictors: list[float] = []
      invalid = False
      for raw in row[3:]:
        numeric = _coerce_float(raw)
        if numeric is None or not math.isfinite(numeric):
          invalid = True
          break
        current_predictors.append(numeric)
      if invalid:
        continue
      id_values.append(str(entity_id))
      time_values.append(str(time_id))
      outcome_values.append(outcome)
      for name, value in zip(predictor_names, current_predictors, strict=True):
        predictor_values[name].append(value)
    if len(outcome_values) < 3:
      raise ExecutionError("xtabond failed")
    column_data: dict[str, object] = {
      panel_id_name: StrVector(tuple(id_values)),
      panel_time_name: StrVector(tuple(time_values)),
      outcome_name: FloatVector(tuple(outcome_values)),
    }
    for name in predictor_names:
      column_data[name] = FloatVector(tuple(predictor_values[name]))
    frame = robjects.DataFrame(column_data)
    pdata_frame = plm.pdata_frame(frame, index=StrVector((panel_id_name, panel_time_name)))
    regressors_rhs = " + ".join((f"lag({outcome_name}, 1)", *predictor_names))
    instrument_rhs = " + ".join((f"lag({outcome_name}, 2:99)", *predictor_names))
    formula = stats.as_formula(f"{outcome_name} ~ {regressors_rhs} | {instrument_rhs}")
    fit = plm.pgmm(
      formula,
      data=pdata_frame,
      model="onestep",
      transformation="d",
    )
    coef_fn = cast(Any, robjects.r["coef"])
    vcov_fn = cast(Any, robjects.r["vcov"])
    names_fn = cast(Any, robjects.r["names"])
    coef_values = np.array(coef_fn(fit), dtype=float).reshape(-1)
    vcov_matrix = np.array(vcov_fn(fit), dtype=float)
    coef_names = tuple(str(name) for name in names_fn(coef_fn(fit)))
    std_errors = np.sqrt(np.diag(vcov_matrix))
    by_name: dict[str, CoefficientEstimate] = {}
    for index, name in enumerate(coef_names):
      value = float(coef_values[index])
      std_error = float(std_errors[index])
      statistic = value / std_error if math.isfinite(std_error) and std_error > 0.0 else None
      by_name[name] = CoefficientEstimate(
        name=name,
        value=value,
        standard_error=std_error if math.isfinite(std_error) else None,
        statistic=statistic if isinstance(statistic, float) and math.isfinite(statistic) else None,
        p_value=None,
      )
    ordered: list[CoefficientEstimate] = []
    lag_name = f"L1.{outcome_name}"
    lag_r_name = f"lag({outcome_name}, 1)"
    for name in (*predictor_names, lag_name):
      candidate = by_name.get(name, by_name.get(lag_r_name if name == lag_name else name))
      if candidate is None:
        continue
      ordered.append(
        CoefficientEstimate(
          name=lag_name if name == lag_name else name,
          value=candidate.value,
          standard_error=candidate.standard_error,
          statistic=candidate.statistic,
          p_value=candidate.p_value,
        )
      )
    if len(ordered) != len((*predictor_names, lag_name)):
      raise ExecutionError("xtabond failed")
    return _XtAbondFitResult(covariance=cov_label, coefficients=tuple(ordered))
  except ExecutionError:
    raise
  except Exception as exc:
    raise ExecutionError("xtabond failed") from exc


def _did_predictions(
  *,
  rows: tuple[tuple[object, ...], ...],
  id_variable: str,
  time_variable: str,
  control_names: tuple[str, ...],
  fitted_model: object,
) -> tuple[float | None, ...]:
  entity_ids: list[object] = []
  time_ids: list[object] = []
  controls: list[tuple[float, ...] | None] = []
  treatment_values: list[float] = []
  post_values: list[float] = []
  row_width = 3 + len(control_names) + 2
  for row in rows:
    if len(row) != row_width:
      return tuple(None for _ in rows)
    entity_id = row[0]
    time_id = row[1]
    control_start = 3
    control_end = control_start + len(control_names)
    treatment_raw = row[control_end]
    post_raw = row[control_end + 1]
    if entity_id is None or time_id is None:
      entity_ids.append(entity_id)
      time_ids.append(time_id)
      controls.append(None)
      treatment_values.append(float("nan"))
      post_values.append(float("nan"))
      continue
    control_row: list[float] = []
    invalid = False
    for raw in row[control_start:control_end]:
      numeric = _coerce_float(raw)
      if numeric is None:
        invalid = True
        break
      control_row.append(numeric)
    treatment = _coerce_float(treatment_raw)
    post = _coerce_float(post_raw)
    if invalid or treatment is None or post is None:
      entity_ids.append(entity_id)
      time_ids.append(time_id)
      controls.append(None)
      treatment_values.append(float("nan"))
      post_values.append(float("nan"))
      continue
    entity_ids.append(entity_id)
    time_ids.append(time_id)
    controls.append(tuple(control_row))
    treatment_values.append(treatment)
    post_values.append(post)

  interaction_name = "__tabdat_did_interaction"
  frame_data: dict[str, object] = {
    id_variable: entity_ids,
    time_variable: time_ids,
  }
  for index, control in enumerate(control_names):
    frame_data[control] = tuple(
      row[index] if row is not None and index < len(row) else np.nan for row in controls
    )
  frame_data[interaction_name] = tuple(
    treat * post if math.isfinite(treat) and math.isfinite(post) else np.nan
    for treat, post in zip(treatment_values, post_values, strict=True)
  )
  model_frame = _data_frame(frame_data, id_variable, time_variable)
  try:
    prediction_frame = model_frame[[*control_names, interaction_name]]
    predicted = cast(Any, fitted_model).predict(exog=prediction_frame)
    predicted_values = predicted.to_numpy().reshape(-1)
  except Exception:
    return tuple(None for _ in rows)
  values: list[float | None] = []
  for value in predicted_values:
    numeric = _to_float_allow_inf(value)
    values.append(numeric)
  return tuple(values)


def _panel_coefficient_estimates(
  predictor_names: tuple[str, ...],
  fitted: object,
) -> tuple[CoefficientEstimate, ...]:
  names = tuple(str(name) for name in getattr(getattr(fitted, "params", None), "index", ()))
  params = _parameter_vector(getattr(fitted, "params", None), "xtreg")
  standard_errors = _optional_float_sequence(getattr(fitted, "std_errors", None))
  statistics = _optional_float_sequence(getattr(fitted, "tstats", None))
  p_values = _optional_float_sequence(getattr(fitted, "pvalues", None))
  if len(params) != len(names):
    raise ExecutionError("xtreg failed")
  coefficients_by_name = {
    name: CoefficientEstimate(
      name=name,
      value=value,
      standard_error=_optional_sequence_value(standard_errors, index),
      statistic=_optional_sequence_value(statistics, index),
      p_value=_optional_sequence_value(p_values, index),
    )
    for index, (name, value) in enumerate(zip(names, params, strict=True))
  }
  coefficients = tuple(
    coefficients_by_name[predictor]
    for predictor in predictor_names
    if predictor in coefficients_by_name
  )
  if len(coefficients) != len(predictor_names):
    raise ExecutionError("xtreg failed")
  return coefficients


def _parameter_vector(values: object, command_name: str) -> np.ndarray:
  if values is None:
    raise ExecutionError(f"{command_name} failed")
  if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
    raise ExecutionError(f"{command_name} failed")
  try:
    numbers = np.array([float(value) for value in values], dtype=float)
  except Exception as exc:
    raise ExecutionError(f"{command_name} failed") from exc
  if numbers.ndim != 1 or numbers.size == 0:
    raise ExecutionError(f"{command_name} failed")
  if np.isnan(numbers).any():
    raise ExecutionError(f"{command_name} failed")
  return numbers


def _covariance_matrix(values: object, command_name: str) -> np.ndarray:
  if values is None:
    raise ExecutionError(f"{command_name} failed")
  to_numpy = getattr(values, "to_numpy", None)
  if not callable(to_numpy):
    raise ExecutionError(f"{command_name} failed")
  try:
    matrix = np.array(to_numpy(), dtype=float)
  except Exception as exc:
    raise ExecutionError(f"{command_name} failed") from exc
  if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
    raise ExecutionError(f"{command_name} failed")
  if np.isnan(matrix).any():
    raise ExecutionError(f"{command_name} failed")
  return matrix


def _data_frame(data: dict[str, object], id_name: str, time_name: str) -> Any:
  import pandas as pd

  frame = pd.DataFrame(data)
  return frame.set_index([id_name, time_name])


def _fitted_parameter_names(fitted_model: object) -> tuple[str, ...]:
  raw_names = getattr(getattr(fitted_model, "model", None), "exog_names", None)
  if isinstance(raw_names, list | tuple) and raw_names:
    return tuple(str(name) for name in raw_names)
  parameter_count = len(_parameter_vector(getattr(fitted_model, "params", None), "estimation"))
  return tuple(f"param_{index}" for index in range(parameter_count))


def _zero_inflated_row_columns(
  *,
  outcome: str,
  predictors: tuple[str, ...],
  inflate_predictors: tuple[str, ...],
  cluster_variable: str | None,
) -> tuple[str, ...]:
  columns: list[str] = [outcome, *predictors, *inflate_predictors]
  if cluster_variable is not None:
    columns.append(cluster_variable)
  return tuple(columns)


def _zero_inflated_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
  inflate_predictor_count: int,
  has_cluster: bool,
) -> tuple[
  tuple[float, ...],
  tuple[tuple[float, ...], ...],
  tuple[tuple[float, ...], ...],
  tuple[object, ...] | None,
  bool,
]:
  outcomes: list[float] = []
  predictors: list[tuple[float, ...]] = []
  inflation_predictors: list[tuple[float, ...]] = []
  clusters: list[object] = []
  missing_cluster_detected = False
  row_width = 1 + predictor_count + inflate_predictor_count + (1 if has_cluster else 0)
  for row in rows:
    if len(row) != row_width:
      continue
    predictor_end = 1 + predictor_count
    inflation_end = predictor_end + inflate_predictor_count
    cluster_value = row[inflation_end] if has_cluster else None
    if (
      row[0] is None
      or any(value is None for value in row[1:predictor_end])
      or any(value is None for value in row[predictor_end:inflation_end])
    ):
      continue
    if has_cluster and cluster_value is None:
      missing_cluster_detected = True
      continue
    outcome = _coerce_float(row[0])
    predictor_values = tuple(
      value for value in (_coerce_float(raw) for raw in row[1:predictor_end]) if value is not None
    )
    inflation_values = tuple(
      value
      for value in (_coerce_float(raw) for raw in row[predictor_end:inflation_end])
      if value is not None
    )
    if outcome is None:
      continue
    if len(predictor_values) != predictor_count or len(inflation_values) != inflate_predictor_count:
      continue
    if not math.isfinite(outcome):
      continue
    if any(not math.isfinite(value) for value in (*predictor_values, *inflation_values)):
      continue
    outcomes.append(outcome)
    predictors.append(predictor_values)
    inflation_predictors.append(inflation_values)
    if has_cluster:
      clusters.append(cluster_value)
  return (
    tuple(outcomes),
    tuple(predictors),
    tuple(inflation_predictors),
    tuple(clusters) if has_cluster else None,
    missing_cluster_detected,
  )


def _binary_predictions(
  *,
  rows: tuple[tuple[object, ...], ...],
  fitted_model: object,
  predictor_count: int,
  include_intercept: bool,
  kind: Literal["xb", "pr"],
) -> tuple[float | None, ...]:
  row_values: list[float | None] = [None for _ in rows]
  complete_indexes: list[int] = []
  complete_predictors: list[tuple[float, ...]] = []
  for row_index, row in enumerate(rows):
    if len(row) != predictor_count:
      raise ExecutionError("predict failed")
    if any(value is None for value in row):
      continue
    predictor_values = tuple(
      value for value in (_coerce_float(raw_value) for raw_value in row) if value is not None
    )
    if len(predictor_values) != predictor_count:
      continue
    if any(not math.isfinite(value) for value in predictor_values):
      continue
    complete_indexes.append(row_index)
    complete_predictors.append(predictor_values)
  if complete_predictors:
    design = np.array(
      _design_matrix(tuple(complete_predictors), include_intercept=include_intercept),
      dtype=float,
    )
    try:
      model = cast(Any, fitted_model).model
      params = cast(Any, fitted_model).params
      which = "linear" if kind == "xb" else "mean"
      predicted = np.array(model.predict(params, design, which=which), dtype=float)
    except Exception:
      try:
        linear = kind == "xb"
        predicted = np.array(cast(Any, fitted_model).predict(design, linear=linear), dtype=float)
      except Exception as exc:
        raise ExecutionError("predict failed") from exc
    if predicted.ndim != 1 or len(predicted) != len(complete_indexes):
      raise ExecutionError("predict failed")
    for row_index, value in zip(complete_indexes, predicted, strict=True):
      float_value = float(value)
      row_values[row_index] = float_value if math.isfinite(float_value) else None
  return tuple(row_values)


def _qreg_predictions(
  *,
  rows: tuple[tuple[object, ...], ...],
  fitted_model: object,
  predictor_count: int,
  include_intercept: bool,
) -> tuple[float | None, ...]:
  row_values: list[float | None] = [None for _ in rows]
  complete_indexes: list[int] = []
  complete_predictors: list[tuple[float, ...]] = []
  for row_index, row in enumerate(rows):
    if len(row) != predictor_count:
      raise ExecutionError("predict failed")
    if any(value is None for value in row):
      continue
    predictor_values = tuple(
      value for value in (_coerce_float(raw_value) for raw_value in row) if value is not None
    )
    if len(predictor_values) != predictor_count:
      continue
    if any(not math.isfinite(value) for value in predictor_values):
      continue
    complete_indexes.append(row_index)
    complete_predictors.append(predictor_values)
  if complete_predictors:
    design = np.array(
      _design_matrix(tuple(complete_predictors), include_intercept=include_intercept),
      dtype=float,
    )
    try:
      predicted = np.array(cast(Any, fitted_model).predict(design), dtype=float)
    except Exception as exc:
      raise ExecutionError("predict failed") from exc
    if predicted.ndim != 1 or len(predicted) != len(complete_indexes):
      raise ExecutionError("predict failed")
    for row_index, value in zip(complete_indexes, predicted, strict=True):
      float_value = float(value)
      row_values[row_index] = float_value if math.isfinite(float_value) else None
  return tuple(row_values)


def _poisson_predictions(
  *,
  rows: tuple[tuple[object, ...], ...],
  fitted_model: object,
  predictor_count: int,
  include_intercept: bool,
  kind: Literal["xb", "mean"],
) -> tuple[float | None, ...]:
  row_values: list[float | None] = [None for _ in rows]
  complete_indexes: list[int] = []
  complete_predictors: list[tuple[float, ...]] = []
  for row_index, row in enumerate(rows):
    if len(row) != predictor_count:
      raise ExecutionError("predict failed")
    if any(value is None for value in row):
      continue
    predictor_values = tuple(
      value for value in (_coerce_float(raw_value) for raw_value in row) if value is not None
    )
    if len(predictor_values) != predictor_count:
      continue
    if any(not math.isfinite(value) for value in predictor_values):
      continue
    complete_indexes.append(row_index)
    complete_predictors.append(predictor_values)
  if complete_predictors:
    design = np.array(
      _design_matrix(tuple(complete_predictors), include_intercept=include_intercept),
      dtype=float,
    )
    try:
      model = cast(Any, fitted_model).model
      params = cast(Any, fitted_model).params
      which = "linear" if kind == "xb" else "mean"
      predicted = np.array(model.predict(params, design, which=which), dtype=float)
    except Exception:
      try:
        linear = kind == "xb"
        predicted = np.array(cast(Any, fitted_model).predict(design, linear=linear), dtype=float)
      except Exception as exc:
        raise ExecutionError("predict failed") from exc
    if predicted.ndim != 1 or len(predicted) != len(complete_indexes):
      raise ExecutionError("predict failed")
    for row_index, value in zip(complete_indexes, predicted, strict=True):
      float_value = float(value)
      row_values[row_index] = float_value if math.isfinite(float_value) else None
  return tuple(row_values)


def _nbreg_predictions(
  *,
  rows: tuple[tuple[object, ...], ...],
  fitted_model: object,
  predictor_count: int,
  include_intercept: bool,
  kind: Literal["xb", "mean"],
) -> tuple[float | None, ...]:
  row_values: list[float | None] = [None for _ in rows]
  complete_indexes: list[int] = []
  complete_predictors: list[tuple[float, ...]] = []
  for row_index, row in enumerate(rows):
    if len(row) != predictor_count:
      raise ExecutionError("predict failed")
    if any(value is None for value in row):
      continue
    predictor_values = tuple(
      value for value in (_coerce_float(raw_value) for raw_value in row) if value is not None
    )
    if len(predictor_values) != predictor_count:
      continue
    if any(not math.isfinite(value) for value in predictor_values):
      continue
    complete_indexes.append(row_index)
    complete_predictors.append(predictor_values)
  if complete_predictors:
    design = np.array(
      _design_matrix(tuple(complete_predictors), include_intercept=include_intercept),
      dtype=float,
    )
    try:
      model = cast(Any, fitted_model).model
      params = cast(Any, fitted_model).params
      which = "linear" if kind == "xb" else "mean"
      predicted = np.array(model.predict(params, design, which=which), dtype=float)
    except Exception:
      try:
        linear = kind == "xb"
        predicted = np.array(cast(Any, fitted_model).predict(design, linear=linear), dtype=float)
      except Exception as exc:
        raise ExecutionError("predict failed") from exc
    if predicted.ndim != 1 or len(predicted) != len(complete_indexes):
      raise ExecutionError("predict failed")
    for row_index, value in zip(complete_indexes, predicted, strict=True):
      float_value = float(value)
      row_values[row_index] = float_value if math.isfinite(float_value) else None
  return tuple(row_values)


def _zero_inflated_predictions(
  *,
  rows: tuple[tuple[object, ...], ...],
  inflation_rows: tuple[tuple[object, ...], ...],
  fitted_model: object,
  predictor_count: int,
  inflate_predictor_count: int,
  include_intercept: bool,
  kind: Literal["xb", "mean"],
) -> tuple[float | None, ...]:
  if len(rows) != len(inflation_rows):
    raise ExecutionError("predict failed")
  row_values: list[float | None] = [None for _ in rows]
  complete_indexes: list[int] = []
  complete_predictors: list[tuple[float, ...]] = []
  complete_inflation_predictors: list[tuple[float, ...]] = []
  for row_index, (row, inflation_row) in enumerate(zip(rows, inflation_rows, strict=True)):
    if len(row) != predictor_count or len(inflation_row) != inflate_predictor_count:
      raise ExecutionError("predict failed")
    if any(value is None for value in row) or any(value is None for value in inflation_row):
      continue
    predictor_values = tuple(
      value for value in (_coerce_float(raw_value) for raw_value in row) if value is not None
    )
    inflation_values = tuple(
      value
      for value in (_coerce_float(raw_value) for raw_value in inflation_row)
      if value is not None
    )
    if len(predictor_values) != predictor_count or len(inflation_values) != inflate_predictor_count:
      continue
    if any(not math.isfinite(value) for value in (*predictor_values, *inflation_values)):
      continue
    complete_indexes.append(row_index)
    complete_predictors.append(predictor_values)
    complete_inflation_predictors.append(inflation_values)
  if complete_predictors:
    design = np.array(
      _design_matrix(tuple(complete_predictors), include_intercept=include_intercept),
      dtype=float,
    )
    inflate_design = np.array(
      _design_matrix(tuple(complete_inflation_predictors), include_intercept=include_intercept),
      dtype=float,
    )
    which = "linear" if kind == "xb" else "mean"
    try:
      model = cast(Any, fitted_model).model
      params = cast(Any, fitted_model).params
      predicted = np.array(
        model.predict(params, exog=design, exog_infl=inflate_design, which=which),
        dtype=float,
      )
    except Exception:
      try:
        predicted = np.array(
          cast(Any, fitted_model).predict(exog=design, exog_infl=inflate_design, which=which),
          dtype=float,
        )
      except Exception as exc:
        raise ExecutionError("predict failed") from exc
    if predicted.ndim != 1 or len(predicted) != len(complete_indexes):
      raise ExecutionError("predict failed")
    for row_index, value in zip(complete_indexes, predicted, strict=True):
      float_value = float(value)
      row_values[row_index] = float_value if math.isfinite(float_value) else None
  return tuple(row_values)


def _fit_heckman_with_r(
  *,
  outcomes: tuple[float, ...],
  outcome_predictors: tuple[tuple[float, ...], ...],
  outcome_predictor_names: tuple[str, ...],
  selection_outcomes: tuple[float, ...],
  selection_predictors: tuple[tuple[float, ...], ...],
  selection_predictor_names: tuple[str, ...],
  include_intercept: bool,
  robust: bool,
  cluster_values: tuple[object, ...] | None,
  cluster_variable: str | None,
) -> tuple[str, tuple[CoefficientEstimate, ...], tuple[CoefficientEstimate, ...]]:
  selection_design = np.array(
    _design_matrix(selection_predictors, include_intercept=include_intercept),
    dtype=float,
  )
  selection_array = np.array(selection_outcomes, dtype=float)
  covariance = "nonrobust"
  try:
    selection_model = sm.Probit(selection_array, selection_design)
    if robust:
      selection_fit = selection_model.fit(disp=0, cov_type="HC1")
      covariance = "robust"
    elif cluster_values is not None:
      selection_fit = selection_model.fit(
        disp=0,
        cov_type="cluster",
        cov_kwds={"groups": np.array(cluster_values)},
      )
      covariance = f"cluster({cluster_variable})"
    else:
      selection_fit = selection_model.fit(disp=0)
    xb = np.array(selection_model.predict(selection_fit.params, selection_design, which="linear"))
    cdf = np.maximum(norm.cdf(xb), 1e-12)
    imr = norm.pdf(xb) / cdf
    selected_indexes = [index for index, value in enumerate(selection_outcomes) if value == 1.0]
    if not selected_indexes:
      raise ExecutionError("heckman failed")
    outcome_values = np.array([outcomes[index] for index in selected_indexes], dtype=float)
    outcome_base = np.array([outcome_predictors[index] for index in selected_indexes], dtype=float)
    if include_intercept:
      outcome_base = np.column_stack([np.ones(len(selected_indexes), dtype=float), outcome_base])
    outcome_design = np.column_stack(
      [outcome_base, np.array([imr[index] for index in selected_indexes])]
    )
    outcome_model = sm.OLS(outcome_values, outcome_design)
    if robust:
      outcome_fit = outcome_model.fit(cov_type="HC1")
    elif cluster_values is not None:
      selected_clusters = np.array([cluster_values[index] for index in selected_indexes])
      outcome_fit = outcome_model.fit(cov_type="cluster", cov_kwds={"groups": selected_clusters})
    else:
      outcome_fit = outcome_model.fit()
  except ExecutionError:
    raise
  except Exception as exc:
    raise ExecutionError("heckman failed") from exc
  selection_names = (
    ("intercept", *selection_predictor_names) if include_intercept else selection_predictor_names
  )
  outcome_base_names = (
    ("intercept", *outcome_predictor_names) if include_intercept else outcome_predictor_names
  )
  outcome_names = (*outcome_base_names, "mills_lambda")
  selection_coefficients = _coefficient_estimates(selection_names, selection_fit)
  outcome_coefficients = _coefficient_estimates(outcome_names, outcome_fit)
  return covariance, outcome_coefficients, selection_coefficients


def _fit_tobit_with_r(
  *,
  outcomes: tuple[float, ...],
  predictors: tuple[tuple[float, ...], ...],
  predictor_names: tuple[str, ...],
  include_intercept: bool,
  lower_limit: float,
  upper_limit: float | None,
  robust: bool,
  cluster_values: tuple[object, ...] | None,
  cluster_variable: str | None,
) -> tuple[str, tuple[CoefficientEstimate, ...]]:
  try:
    from rpy2 import robjects
    from rpy2.robjects import packages
    from rpy2.robjects.vectors import FloatVector, StrVector
  except Exception:
    return _fit_tobit_parametric(
      outcomes=outcomes,
      predictors=predictors,
      predictor_names=predictor_names,
      include_intercept=include_intercept,
      lower_limit=lower_limit,
      upper_limit=upper_limit,
      robust=robust,
      cluster_values=cluster_values,
      cluster_variable=cluster_variable,
    )
  try:
    require_namespace = cast(Any, robjects.r["requireNamespace"])
    if not bool(require_namespace("survival", quietly=True)[0]):
      return _fit_tobit_parametric(
        outcomes=outcomes,
        predictors=predictors,
        predictor_names=predictor_names,
        include_intercept=include_intercept,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
        robust=robust,
        cluster_values=cluster_values,
        cluster_variable=cluster_variable,
      )
    survival = packages.importr("survival")
    stats = packages.importr("stats")
    left_bounds: list[float] = []
    right_bounds: list[float] = []
    for outcome in outcomes:
      if upper_limit is None:
        if outcome <= lower_limit:
          left_bounds.append(float("-inf"))
          right_bounds.append(lower_limit)
        else:
          left_bounds.append(outcome)
          right_bounds.append(outcome)
        continue
      if outcome <= lower_limit:
        left_bounds.append(float("-inf"))
        right_bounds.append(lower_limit)
      elif outcome >= upper_limit:
        left_bounds.append(upper_limit)
        right_bounds.append(float("inf"))
      else:
        left_bounds.append(outcome)
        right_bounds.append(outcome)
    taken_names = set(predictor_names)
    left_name = _unique_internal_name("tabdat_left", taken_names)
    taken_names.add(left_name)
    right_name = _unique_internal_name("tabdat_right", taken_names)
    taken_names.add(right_name)
    cluster_name = _unique_internal_name("tabdat_cluster", taken_names)
    frame_columns: dict[str, object] = {
      left_name: FloatVector(left_bounds),
      right_name: FloatVector(right_bounds),
    }
    for index, predictor in enumerate(predictor_names):
      frame_columns[predictor] = FloatVector(tuple(row[index] for row in predictors))
    frame = robjects.DataFrame(frame_columns)
    cluster_argument = None
    if cluster_values is not None:
      frame_columns[cluster_name] = StrVector(tuple(str(value) for value in cluster_values))
      frame = robjects.DataFrame(frame_columns)
      cluster_argument = frame.rx2(cluster_name)
    rhs = " + ".join(predictor_names)
    if not include_intercept:
      rhs = f"0 + {rhs}"
    formula = stats.as_formula(
      f"survival::Surv({left_name}, {right_name}, type='interval2') ~ {rhs}"
    )
    fit_kwargs: dict[str, object] = {"data": frame, "dist": "gaussian"}
    covariance = "nonrobust"
    if robust:
      fit_kwargs["robust"] = True
      covariance = "robust"
    if cluster_argument is not None:
      fit_kwargs["cluster"] = cluster_argument
      fit_kwargs["robust"] = True
      covariance = f"cluster({cluster_variable})"
    fit = survival.survreg(formula, **fit_kwargs)
    summary_fn = cast(Any, robjects.r["summary"])
    rownames_fn = cast(Any, robjects.r["rownames"])
    summary = summary_fn(fit)
    table = np.array(summary.rx2("table"), dtype=float)
    row_names = tuple(str(name) for name in rownames_fn(summary.rx2("table")))
    if table.ndim != 2 or table.shape[1] < 4:
      raise ExecutionError("tobit failed")
    coefficients_by_name: dict[str, CoefficientEstimate] = {}
    for index, name in enumerate(row_names):
      if name == "Log(scale)":
        continue
      value = float(table[index, 0])
      std_error = float(table[index, 1])
      statistic = float(table[index, 2])
      p_value = float(table[index, 3])
      coefficients_by_name[name] = CoefficientEstimate(
        name=name,
        value=value,
        standard_error=std_error if math.isfinite(std_error) else None,
        statistic=statistic if math.isfinite(statistic) else None,
        p_value=p_value if math.isfinite(p_value) else None,
      )
    ordered_names = ("(Intercept)", *predictor_names) if include_intercept else predictor_names
    coefficients = tuple(
      CoefficientEstimate(
        name=("intercept" if name == "(Intercept)" else name),
        value=coefficients_by_name[name].value,
        standard_error=coefficients_by_name[name].standard_error,
        statistic=coefficients_by_name[name].statistic,
        p_value=coefficients_by_name[name].p_value,
      )
      for name in ordered_names
      if name in coefficients_by_name
    )
    if len(coefficients) != len(ordered_names):
      raise ExecutionError("tobit failed")
    return covariance, coefficients
  except ExecutionError:
    raise
  except Exception as exc:
    try:
      return _fit_tobit_parametric(
        outcomes=outcomes,
        predictors=predictors,
        predictor_names=predictor_names,
        include_intercept=include_intercept,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
        robust=robust,
        cluster_values=cluster_values,
        cluster_variable=cluster_variable,
      )
    except ExecutionError:
      raise ExecutionError("tobit failed") from exc


def _fit_tobit_parametric(
  *,
  outcomes: tuple[float, ...],
  predictors: tuple[tuple[float, ...], ...],
  predictor_names: tuple[str, ...],
  include_intercept: bool,
  lower_limit: float,
  upper_limit: float | None,
  robust: bool,
  cluster_values: tuple[object, ...] | None,
  cluster_variable: str | None,
) -> tuple[str, tuple[CoefficientEstimate, ...]]:
  design = np.array(_design_matrix(predictors, include_intercept=include_intercept), dtype=float)
  outcome_array = np.array(outcomes, dtype=float)

  def observation_log_likelihood(params: np.ndarray) -> np.ndarray:
    beta = params[:-1]
    log_sigma = params[-1]
    sigma = math.exp(float(np.clip(log_sigma, -10.0, 10.0)))
    mu = design @ beta
    z = (outcome_array - mu) / sigma
    logpdf = norm.logpdf(z) - math.log(sigma)

    left_mask = outcome_array <= lower_limit
    if upper_limit is None:
      right_mask = np.zeros_like(left_mask, dtype=bool)
    else:
      right_mask = outcome_array >= upper_limit
    uncensored_mask = ~(left_mask | right_mask)
    log_likelihood = np.zeros_like(outcome_array, dtype=float)
    if np.any(uncensored_mask):
      log_likelihood[uncensored_mask] = logpdf[uncensored_mask]
    if np.any(left_mask):
      left_z = (lower_limit - mu[left_mask]) / sigma
      log_likelihood[left_mask] = norm.logcdf(left_z)
    if np.any(right_mask):
      assert upper_limit is not None
      right_z = (upper_limit - mu[right_mask]) / sigma
      log_likelihood[right_mask] = np.log(np.maximum(1.0 - norm.cdf(right_z), 1e-12))
    return log_likelihood

  def objective(params: np.ndarray) -> float:
    return float(-np.sum(observation_log_likelihood(params)))

  initial = np.zeros(design.shape[1] + 1, dtype=float)
  result = minimize(objective, initial, method="BFGS")
  if not result.success:
    result = minimize(objective, initial, method="L-BFGS-B")
  if not result.success:
    raise ExecutionError("tobit failed")
  hess_inv = _inverse_hessian_matrix(result.hess_inv)
  cov = hess_inv
  if robust or cluster_values is not None:
    cov = _sandwich_covariance(
      params=np.array(result.x, dtype=float),
      observation_log_likelihood=observation_log_likelihood,
      inverse_hessian=hess_inv,
      cluster_values=cluster_values,
    )
  beta = np.array(result.x[:-1], dtype=float)
  se = np.sqrt(np.maximum(np.diag(cov[: design.shape[1], : design.shape[1]]), 0.0))
  names = ("intercept", *predictor_names) if include_intercept else predictor_names
  coefficients: list[CoefficientEstimate] = []
  for index, name in enumerate(names):
    value = float(beta[index])
    se_value = float(se[index]) if index < len(se) else math.nan
    if not math.isfinite(se_value) or se_value <= 0.0:
      coefficients.append(
        CoefficientEstimate(
          name=name,
          value=value,
          standard_error=None,
          statistic=None,
          p_value=None,
        )
      )
      continue
    statistic = value / se_value
    p_value = float(2.0 * (1.0 - norm.cdf(abs(statistic))))
    coefficients.append(
      CoefficientEstimate(
        name=name,
        value=value,
        standard_error=se_value,
        statistic=statistic,
        p_value=p_value,
      )
    )
  covariance = "nonrobust"
  if robust:
    covariance = "robust"
  if cluster_values is not None and cluster_variable is not None:
    covariance = f"cluster({cluster_variable})"
  return covariance, tuple(coefficients)


def _inverse_hessian_matrix(hess_inv: object) -> np.ndarray:
  if hasattr(hess_inv, "todense"):
    return np.array(cast(Any, hess_inv).todense(), dtype=float)
  return np.array(cast(Any, hess_inv), dtype=float)


def _sandwich_covariance(
  *,
  params: np.ndarray,
  observation_log_likelihood: Callable[[np.ndarray], np.ndarray],
  inverse_hessian: np.ndarray,
  cluster_values: tuple[object, ...] | None,
) -> np.ndarray:
  score = _score_matrix(params=params, observation_log_likelihood=observation_log_likelihood)
  if cluster_values is None:
    meat = score.T @ score
  else:
    if len(cluster_values) != score.shape[0]:
      raise ExecutionError("model failed")
    grouped_scores: dict[str, np.ndarray] = {}
    for index, group_value in enumerate(cluster_values):
      key = str(group_value)
      current = grouped_scores.get(key)
      if current is None:
        grouped_scores[key] = score[index].copy()
      else:
        grouped_scores[key] = current + score[index]
    grouped = np.vstack(tuple(grouped_scores.values()))
    meat = grouped.T @ grouped
  return np.asarray(inverse_hessian @ meat @ inverse_hessian, dtype=float)


def _score_matrix(
  *,
  params: np.ndarray,
  observation_log_likelihood: Callable[[np.ndarray], np.ndarray],
  epsilon: float = 1e-6,
) -> np.ndarray:
  score_columns: list[np.ndarray] = []
  for param_index in range(len(params)):
    forward = np.array(params, copy=True)
    backward = np.array(params, copy=True)
    forward[param_index] += epsilon
    backward[param_index] -= epsilon
    forward_ll = observation_log_likelihood(forward)
    backward_ll = observation_log_likelihood(backward)
    score_columns.append((forward_ll - backward_ll) / (2.0 * epsilon))
  return np.asarray(np.column_stack(score_columns), dtype=float)


def _fit_streg_parametric(
  *,
  times: tuple[float, ...],
  failures: tuple[float, ...],
  predictors: tuple[tuple[float, ...], ...],
  predictor_names: tuple[str, ...],
  include_intercept: bool,
  distribution: Literal["weibull", "exponential"],
  robust: bool,
  cluster_values: tuple[object, ...] | None,
  cluster_variable: str | None,
) -> tuple[str, tuple[CoefficientEstimate, ...]]:
  design = np.array(_design_matrix(predictors, include_intercept=include_intercept), dtype=float)
  time_array = np.array(times, dtype=float)
  failure_array = np.array(failures, dtype=float)

  def observation_log_likelihood(params: np.ndarray) -> np.ndarray:
    linear = design @ params[: design.shape[1]]
    rate = np.exp(np.clip(linear, -30.0, 30.0))
    if distribution == "exponential":
      log_likelihood = failure_array * np.log(np.maximum(rate, 1e-12)) - (rate * time_array)
      return np.asarray(log_likelihood, dtype=float)
    log_shape = params[-1]
    shape = math.exp(float(np.clip(log_shape, -10.0, 10.0)))
    log_time = np.log(np.maximum(time_array, 1e-12))
    return np.asarray(
      failure_array
      * (math.log(shape) + np.log(np.maximum(rate, 1e-12)) + ((shape - 1.0) * log_time))
      - (rate * np.power(time_array, shape)),
      dtype=float,
    )

  def objective(params: np.ndarray) -> float:
    return float(-np.sum(observation_log_likelihood(params)))

  initial = np.zeros(design.shape[1] + (0 if distribution == "exponential" else 1), dtype=float)
  result = minimize(objective, initial, method="BFGS")
  if not result.success:
    result = minimize(objective, initial, method="L-BFGS-B")
  if not result.success:
    raise ExecutionError("streg failed")
  fitted = np.array(result.x, dtype=float)
  if distribution == "exponential":
    coefficient_values = fitted
  else:
    coefficient_values = fitted[: design.shape[1]]
  hess_inv = _inverse_hessian_matrix(result.hess_inv)
  cov = hess_inv
  if robust or cluster_values is not None:
    cov = _sandwich_covariance(
      params=np.array(result.x, dtype=float),
      observation_log_likelihood=observation_log_likelihood,
      inverse_hessian=hess_inv,
      cluster_values=cluster_values,
    )
  coefficient_cov = cov[: design.shape[1], : design.shape[1]]
  standard_errors = np.sqrt(np.maximum(np.diag(coefficient_cov), 0.0))
  estimates: list[CoefficientEstimate] = []
  names = ("intercept", *predictor_names) if include_intercept else predictor_names
  for index, name in enumerate(names):
    value = float(coefficient_values[index])
    standard_error_value = (
      float(standard_errors[index]) if index < len(standard_errors) else math.nan
    )
    if not math.isfinite(standard_error_value) or standard_error_value <= 0.0:
      estimates.append(
        CoefficientEstimate(
          name=name,
          value=value,
          standard_error=None,
          statistic=None,
          p_value=None,
        )
      )
      continue
    statistic = value / standard_error_value
    p_value = float(2.0 * (1.0 - norm.cdf(abs(statistic))))
    estimates.append(
      CoefficientEstimate(
        name=name,
        value=value,
        standard_error=standard_error_value,
        statistic=statistic,
        p_value=p_value,
      )
    )
  covariance = "nonrobust"
  if robust:
    covariance = "robust"
  if cluster_values is not None and cluster_variable is not None:
    covariance = f"cluster({cluster_variable})"
  return covariance, tuple(estimates)


def _unique_internal_name(base: str, taken_names: set[str]) -> str:
  if base not in taken_names:
    return base
  index = 2
  while True:
    candidate = f"{base}_{index}"
    if candidate not in taken_names:
      return candidate
    index += 1


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


def _iv_parameter_names(command: IvRegressCommand) -> tuple[str, ...]:
  names: list[str] = []
  if command.include_intercept:
    names.append("intercept")
  names.extend(command.exogenous)
  names.append(command.endogenous)
  return tuple(names)


def _iv_coefficient_estimates(
  parameter_names: Sequence[str],
  fitted: object,
) -> tuple[CoefficientEstimate, ...]:
  params = _required_float_sequence(getattr(fitted, "params", None))
  standard_errors = _optional_float_sequence(
    getattr(fitted, "std_errors", getattr(fitted, "bse", None))
  )
  statistics = _optional_float_sequence(getattr(fitted, "tstats", getattr(fitted, "tvalues", None)))
  p_values = _optional_float_sequence(getattr(fitted, "pvalues", None))
  if len(params) != len(parameter_names):
    raise ExecutionError("ivregress failed")
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


def _to_float_allow_inf(value: object) -> float | None:
  if value is None or isinstance(value, bool):
    return None
  if not isinstance(value, SupportsFloat):
    return None
  try:
    numeric = float(value)
  except (TypeError, ValueError):
    return None
  if math.isnan(numeric):
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


def _nl_predictor_names(
  expression: Expression,
  parameter_names: tuple[str, ...],
) -> tuple[str, ...]:
  names: list[str] = []
  seen = set(parameter_names)
  for identifier in _expression_identifiers(expression):
    if identifier in seen:
      continue
    seen.add(identifier)
    names.append(identifier)
  return tuple(names)


def _expression_identifiers(expression: Expression) -> tuple[str, ...]:
  if isinstance(expression, IdentifierExpression):
    return (expression.name,)
  if isinstance(expression, (NumberExpression, StringExpression)):
    return ()
  if isinstance(expression, UnaryExpression):
    return _expression_identifiers(expression.operand)
  if isinstance(expression, BinaryExpression):
    return (*_expression_identifiers(expression.left), *_expression_identifiers(expression.right))
  if isinstance(expression, FunctionCallExpression):
    values: list[str] = []
    for argument in expression.arguments:
      values.extend(_expression_identifiers(argument))
    return tuple(values)
  return ()


def _nl_sample(
  *,
  rows: tuple[tuple[object, ...], ...],
  predictor_count: int,
) -> tuple[tuple[float, ...], tuple[tuple[float, ...], ...]]:
  outcomes: list[float] = []
  predictors: list[tuple[float, ...]] = []
  row_width = predictor_count + 1
  for row in rows:
    if len(row) != row_width:
      raise ExecutionError("nl failed")
    raw_outcome = row[0]
    raw_predictors = row[1:]
    if raw_outcome is None or any(value is None for value in raw_predictors):
      continue
    outcome = _coerce_float(raw_outcome)
    predictor_values = tuple(_coerce_float(value) for value in raw_predictors)
    if outcome is None or any(value is None for value in predictor_values):
      continue
    complete_predictors = tuple(value for value in predictor_values if value is not None)
    outcomes.append(outcome)
    predictors.append(complete_predictors)
  return tuple(outcomes), tuple(predictors)


def _nl_covariance_matrix(
  *,
  jacobian: np.ndarray,
  residuals: np.ndarray,
  robust: bool,
) -> tuple[np.ndarray, str]:
  if jacobian.ndim != 2:
    raise ExecutionError("nl failed")
  n_obs, n_params = jacobian.shape
  if n_obs == 0 or n_params == 0:
    raise ExecutionError("nl failed")
  xtx = jacobian.T @ jacobian
  try:
    xtx_inv = np.linalg.pinv(xtx)
  except Exception as exc:
    raise ExecutionError("nl failed") from exc
  if robust:
    # HC1 sandwich covariance over local linearization Jacobian.
    scale = float(n_obs) / float(max(n_obs - n_params, 1))
    weighted = jacobian * residuals[:, np.newaxis]
    meat = weighted.T @ weighted
    covariance = scale * (xtx_inv @ meat @ xtx_inv)
    return covariance, "robust"
  sigma2 = float(np.dot(residuals, residuals)) / float(max(n_obs - n_params, 1))
  return sigma2 * xtx_inv, "nonrobust"


def _nl_coefficient_estimates(
  *,
  parameter_names: tuple[str, ...],
  values: np.ndarray,
  covariance: np.ndarray,
  residual_df: int,
) -> tuple[CoefficientEstimate, ...]:
  if values.ndim != 1 or covariance.ndim != 2:
    raise ExecutionError("nl failed")
  if len(parameter_names) != len(values) or covariance.shape[0] != covariance.shape[1]:
    raise ExecutionError("nl failed")
  z_dist = norm()
  estimates: list[CoefficientEstimate] = []
  for index, name in enumerate(parameter_names):
    value = float(values[index])
    variance = float(covariance[index, index]) if index < covariance.shape[0] else float("nan")
    std_error = math.sqrt(variance) if math.isfinite(variance) and variance >= 0.0 else None
    statistic: float | None = None
    p_value: float | None = None
    if std_error is not None and std_error > 0.0:
      statistic = value / std_error
      p_value = 2.0 * (1.0 - z_dist.cdf(abs(statistic)))
    estimates.append(
      CoefficientEstimate(
        name=name,
        value=value,
        standard_error=std_error,
        statistic=statistic,
        p_value=p_value,
      )
    )
  return tuple(estimates)


def _evaluate_nl_expression(
  expression: Expression,
  *,
  predictor_row: tuple[float, ...],
  predictor_index: dict[str, int],
  params: np.ndarray,
  param_index: dict[str, int],
) -> float:
  if isinstance(expression, NumberExpression):
    return float(expression.value)
  if isinstance(expression, IdentifierExpression):
    if expression.name in param_index:
      return float(params[param_index[expression.name]])
    if expression.name in predictor_index:
      return float(predictor_row[predictor_index[expression.name]])
    raise ExecutionError(f"nl unknown variable: {expression.name}")
  if isinstance(expression, UnaryExpression):
    if expression.operator == "-":
      return -_evaluate_nl_expression(
        expression.operand,
        predictor_row=predictor_row,
        predictor_index=predictor_index,
        params=params,
        param_index=param_index,
      )
    raise ExecutionError("nl failed")
  if isinstance(expression, BinaryExpression):
    left = _evaluate_nl_expression(
      expression.left,
      predictor_row=predictor_row,
      predictor_index=predictor_index,
      params=params,
      param_index=param_index,
    )
    right = _evaluate_nl_expression(
      expression.right,
      predictor_row=predictor_row,
      predictor_index=predictor_index,
      params=params,
      param_index=param_index,
    )
    if expression.operator == "+":
      return left + right
    if expression.operator == "-":
      return left - right
    if expression.operator == "*":
      return left * right
    if expression.operator == "/":
      return left / right
    raise ExecutionError("nl supports arithmetic expressions only")
  if isinstance(expression, FunctionCallExpression):
    args = tuple(
      _evaluate_nl_expression(
        argument,
        predictor_row=predictor_row,
        predictor_index=predictor_index,
        params=params,
        param_index=param_index,
      )
      for argument in expression.arguments
    )
    return _evaluate_nl_function(expression.name.lower(), args)
  raise ExecutionError("nl failed")


def _evaluate_nl_function(name: str, arguments: tuple[float, ...]) -> float:
  if name == "abs" and len(arguments) == 1:
    return abs(arguments[0])
  if name == "ceil" and len(arguments) == 1:
    return float(math.ceil(arguments[0]))
  if name == "floor" and len(arguments) == 1:
    return float(math.floor(arguments[0]))
  if name == "ln" and len(arguments) == 1:
    return math.log(arguments[0])
  if name == "log" and len(arguments) == 1:
    return math.log10(arguments[0])
  if name == "round" and len(arguments) in {1, 2}:
    if len(arguments) == 2:
      return float(round(arguments[0], int(arguments[1])))
    return float(round(arguments[0]))
  if name == "sqrt" and len(arguments) == 1:
    return math.sqrt(arguments[0])
  if name == "exp" and len(arguments) == 1:
    return math.exp(arguments[0])
  raise ExecutionError(f"nl unsupported function: {name}")


def _nl_predictions(
  *,
  expression: Expression,
  rows: tuple[tuple[object, ...], ...],
  predictor_names: tuple[str, ...],
  parameter_names: tuple[str, ...],
  parameter_values: tuple[float, ...],
) -> tuple[float | None, ...]:
  parameter_vector = np.array(parameter_values, dtype=float)
  predictor_index = {name: index for index, name in enumerate(predictor_names)}
  param_index = {name: index for index, name in enumerate(parameter_names)}
  values: list[float | None] = []
  for row in rows:
    if len(row) != len(predictor_names):
      raise ExecutionError("predict failed")
    if any(value is None for value in row):
      values.append(None)
      continue
    predictor_row = tuple(_coerce_float(value) for value in row)
    if any(value is None for value in predictor_row):
      values.append(None)
      continue
    complete_row = tuple(value for value in predictor_row if value is not None)
    values.append(
      _evaluate_nl_expression(
        expression,
        predictor_row=complete_row,
        predictor_index=predictor_index,
        params=parameter_vector,
        param_index=param_index,
      )
    )
  return tuple(values)


def _nl_constant_predictions(
  *,
  expression: Expression,
  parameter_names: tuple[str, ...],
  parameter_values: tuple[float, ...],
  row_count: int,
) -> tuple[float | None, ...]:
  parameter_vector = np.array(parameter_values, dtype=float)
  param_index = {name: index for index, name in enumerate(parameter_names)}
  value = _evaluate_nl_expression(
    expression,
    predictor_row=(),
    predictor_index={},
    params=parameter_vector,
    param_index=param_index,
  )
  return tuple(value for _ in range(row_count))


def _format_expression(expression: Expression) -> str:
  if isinstance(expression, IdentifierExpression):
    return expression.name
  if isinstance(expression, NumberExpression):
    return str(expression.value)
  if isinstance(expression, StringExpression):
    return repr(expression.value)
  if isinstance(expression, UnaryExpression):
    return f"-({_format_expression(expression.operand)})"
  if isinstance(expression, BinaryExpression):
    return (
      f"({_format_expression(expression.left)} {expression.operator} "
      f"{_format_expression(expression.right)})"
    )
  if isinstance(expression, FunctionCallExpression):
    args = ", ".join(_format_expression(argument) for argument in expression.arguments)
    return f"{expression.name}({args})"
  return "<expr>"


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

"""Command executor and session state."""

import hashlib
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, SupportsFloat, cast

import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS, IVGMM
from linearmodels.panel import PanelOLS, RandomEffects
from scipy.stats import chi2, norm
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
  DropCommand,
  EstatCommand,
  ExitCommand,
  ExportCommand,
  ExportResult,
  GenerateCommand,
  HeadCommand,
  HeckmanCommand,
  HeckmanRegressionResult,
  HistogramCommand,
  IvRegressCommand,
  IvRegressionResult,
  JoinCommand,
  KeepCommand,
  LoadResult,
  LogitCommand,
  LogitRegressionResult,
  PanelCommand,
  PanelMetadata,
  PanelResult,
  PlotResult,
  PredictCommand,
  PreviewResult,
  ProbitCommand,
  ProbitRegressionResult,
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
  TobitCommand,
  TobitRegressionResult,
  TransformResult,
  UseCommand,
  XtDataCommand,
  XtRegCommand,
  XtRegressionResult,
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
class _BinaryRegressionState:
  family: Literal["logit", "probit"]
  outcome_variable: str
  predictor_names: tuple[str, ...]
  include_intercept: bool
  fitted_model: object


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
  binary_regression: _BinaryRegressionState | None = None
  iv_regression: _IvRegressionState | None = None
  cf_regression: _CfRegressionState | None = None
  xt_regressions: _XtModelCache = field(default_factory=_XtModelCache)


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

    if isinstance(command, LogitCommand):
      return self._execute_logit(command)

    if isinstance(command, ProbitCommand):
      return self._execute_probit(command)

    if isinstance(command, TobitCommand):
      return self._execute_tobit(command)

    if isinstance(command, HeckmanCommand):
      return self._execute_heckman(command)

    if isinstance(command, IvRegressCommand):
      return self._execute_ivregress(command)

    if isinstance(command, CfRegressCommand):
      return self._execute_cfregress(command)

    if isinstance(command, XtRegCommand):
      return self._execute_xtreg(command)

    if isinstance(command, XtDataCommand):
      return self._execute_xtdata(command)

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
    self.state.binary_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
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
    self.state.binary_regression = _BinaryRegressionState(
      family="logit",
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
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
    self.state.binary_regression = _BinaryRegressionState(
      family="probit",
      outcome_variable=command.outcome,
      predictor_names=command.predictors,
      include_intercept=command.include_intercept,
      fitted_model=fitted,
    )
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
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
    self.state.binary_regression = None
    self.state.iv_regression = _IvRegressionState(
      estimator=command.estimator,
      fitted_model=fitted,
    )
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
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
    self.state.binary_regression = None
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
    raise ExecutionError("predict requires a prior regress or cfregress model")

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
    self.state.binary_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
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
    self.state.binary_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
    self.state.xt_regressions = _XtModelCache()
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
      if regression is None:
        raise ExecutionError("estat requires a prior regress model")
      return _estat_residuals_table(regression.fitted_model)
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
    self.state.binary_regression = None
    self.state.iv_regression = None
    self.state.cf_regression = None
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
  except Exception as exc:
    raise ExecutionError("tobit failed") from exc
  try:
    require_namespace = cast(Any, robjects.r["requireNamespace"])
    if not bool(require_namespace("survival", quietly=True)[0]):
      raise ExecutionError("tobit failed")
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
    raise ExecutionError("tobit failed") from exc


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

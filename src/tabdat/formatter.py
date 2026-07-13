"""Terminal formatting for structured command results."""

import base64
import json
import math
from collections.abc import Iterable, Sequence
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path

from pydantic import TypeAdapter

from tabdat.errors import (
  BackendExecutionError,
  ExecutionError,
  NoActiveDatasetError,
  ParseError,
  ReservedNameError,
  TabDatError,
  TypeMismatchExecutionError,
  UnknownTableError,
  UnknownVariableError,
)
from tabdat.models import (
  ActivateResult,
  BayesMcmcResult,
  BayesRegressionResult,
  CfRegressionResult,
  CodebookResult,
  CommandCatalogResult,
  CommandEffectCatalogResult,
  CommandExplainResult,
  CommandSchemaResult,
  CountResult,
  CvelasticnetRegressionResult,
  CvlassoRegressionResult,
  CvridgeRegressionResult,
  DescribeResult,
  DidRegressionResult,
  DmlRegressionResult,
  DrDidRegressionResult,
  ElasticnetRegressionResult,
  ExportResult,
  HeckmanRegressionResult,
  HelpTopicResult,
  IvRegressionResult,
  LassoRegressionResult,
  LincomResult,
  LoadResult,
  LogitRegressionResult,
  NbregRegressionResult,
  NlRegressionResult,
  PanelResult,
  PlotResult,
  PoissonRegressionResult,
  PostlassoRegressionResult,
  PreviewResult,
  ProbitRegressionResult,
  QregRegressionResult,
  RegressionResult,
  Result,
  RidgeRegressionResult,
  SaveResult,
  SetResult,
  SpatialRegressionResult,
  SqlCreateResult,
  StatusResult,
  StregRegressionResult,
  SummarizeResult,
  TableResult,
  TestResult,
  TobitRegressionResult,
  TransformResult,
  TtestGroupStats,
  TtestResult,
  XtAbondRegressionResult,
  XtLogitRegressionResult,
  XtRegressionResult,
  ZinbRegressionResult,
  ZipRegressionResult,
)
from tabdat.script import ScriptError

RESULT_TYPE_LABELS: dict[type[object], str] = {
  CommandCatalogResult: "CommandCatalogResult",
  CommandEffectCatalogResult: "CommandEffectCatalogResult",
  CommandSchemaResult: "CommandSchemaResult",
  HelpTopicResult: "HelpTopicResult",
  CommandExplainResult: "CommandExplainResult",
  LoadResult: "LoadResult",
  ActivateResult: "ActivateResult",
  DescribeResult: "DescribeResult",
  StatusResult: "StatusResult",
  SummarizeResult: "SummarizeResult",
  CodebookResult: "CodebookResult",
  CountResult: "CountResult",
  PreviewResult: "PreviewResult",
  TransformResult: "TransformResult",
  RegressionResult: "RegressionResult",
  LassoRegressionResult: "LassoRegressionResult",
  PostlassoRegressionResult: "PostlassoRegressionResult",
  RidgeRegressionResult: "RidgeRegressionResult",
  ElasticnetRegressionResult: "ElasticnetRegressionResult",
  CvlassoRegressionResult: "CvlassoRegressionResult",
  CvridgeRegressionResult: "CvridgeRegressionResult",
  CvelasticnetRegressionResult: "CvelasticnetRegressionResult",
  BayesRegressionResult: "BayesRegressionResult",
  SpatialRegressionResult: "SpatialRegressionResult",
  QregRegressionResult: "QregRegressionResult",
  LogitRegressionResult: "LogitRegressionResult",
  ProbitRegressionResult: "ProbitRegressionResult",
  TobitRegressionResult: "TobitRegressionResult",
  HeckmanRegressionResult: "HeckmanRegressionResult",
  NlRegressionResult: "NlRegressionResult",
  PoissonRegressionResult: "PoissonRegressionResult",
  NbregRegressionResult: "NbregRegressionResult",
  ZipRegressionResult: "ZipRegressionResult",
  ZinbRegressionResult: "ZinbRegressionResult",
  StregRegressionResult: "StregRegressionResult",
  IvRegressionResult: "IvRegressionResult",
  XtRegressionResult: "XtRegressionResult",
  XtLogitRegressionResult: "XtLogitRegressionResult",
  XtAbondRegressionResult: "XtAbondRegressionResult",
  DidRegressionResult: "DidRegressionResult",
  DrDidRegressionResult: "DrDidRegressionResult",
  DmlRegressionResult: "DmlRegressionResult",
  CfRegressionResult: "CfRegressionResult",
  PanelResult: "PanelResult",
  SqlCreateResult: "SqlCreateResult",
  TableResult: "TableResult",
  PlotResult: "PlotResult",
  SetResult: "SetResult",
  SaveResult: "SaveResult",
  ExportResult: "ExportResult",
  BayesMcmcResult: "BayesMcmcResult",
  TestResult: "TestResult",
  LincomResult: "LincomResult",
  TtestResult: "TtestResult",
}

ERROR_TYPE_LABELS: dict[type[object], str] = {
  TabDatError: "TabDatError",
  ParseError: "ParseError",
  ExecutionError: "ExecutionError",
  NoActiveDatasetError: "NoActiveDatasetError",
  UnknownVariableError: "UnknownVariableError",
  TypeMismatchExecutionError: "TypeMismatchExecutionError",
  UnknownTableError: "UnknownTableError",
  ReservedNameError: "ReservedNameError",
  BackendExecutionError: "BackendExecutionError",
  ScriptError: "ScriptError",
}


def format_result(result: Result) -> str:
  if isinstance(result, CommandEffectCatalogResult):
    return "\n".join(
      _table(
        ("Command", "Effects"),
        ((entry.name, ", ".join(entry.effects)) for entry in result.commands),
      )
    )

  if isinstance(result, CommandSchemaResult):
    args_str = ", ".join(
      f"{arg.name}{'' if arg.required else ' (optional)'}" for arg in result.arguments
    )
    opts_str = ", ".join(
      f"{opt.name}{'' if opt.required else ' (optional)'}" for opt in result.options
    )
    return (
      f"Command: {result.name}\n"
      f"Syntax: {result.syntax}\n"
      f"Help Topic: {result.help_topic or '.'}\n"
      f"Arguments: {args_str or '.'}\n"
      f"Options: {opts_str or '.'}"
    )

  if isinstance(result, CommandExplainResult):
    return f"Command: {result.command_name}\nExecution: {result.execution}"

  if isinstance(result, HelpTopicResult):
    return result.text

  if isinstance(result, CommandCatalogResult):
    return "\n".join(
      _table(
        ("Command", "Help"),
        ((entry.name, entry.help_topic or ".") for entry in result.commands),
      )
    )

  if isinstance(result, LoadResult):
    dataset = result.dataset
    mode = (
      f", lazy={dataset.lazy_engine}"
      if dataset.execution_mode == "lazy" and dataset.lazy_engine is not None
      else ""
    )
    return (
      f"Loaded: {_display_path(dataset.path)} "
      f"({_row_count(dataset.row_count)} rows, {dataset.column_count} columns{mode})"
    )

  if isinstance(result, ActivateResult):
    dataset = result.dataset
    return (
      f"Activated: {result.table_name} "
      f"({_row_count(dataset.row_count)} rows, {dataset.column_count} columns)"
    )

  if isinstance(result, DescribeResult):
    dataset = result.dataset
    lines = [
      f"Dataset: {_display_path(dataset.path)}",
      f"Rows: {_row_count(dataset.row_count)}",
      f"Columns: {dataset.column_count}",
      "",
    ]
    lines.extend(
      _table(
        ("Variable", "Type"),
        ((column.name, column.data_type) for column in dataset.columns),
      )
    )
    return "\n".join(lines)

  if isinstance(result, StatusResult):
    source = result.source
    materialization = (
      "materialized"
      if result.execution_mode == "eager"
      else "deferred"
      if result.execution_mode == "lazy"
      else "none"
    )
    reason = {
      "polars_fallback": "polars fallback",
      "eager_operation": "eager operation",
    }.get(result.last_materialization_reason or "", "none")
    return "\n".join(
      (
        f"Backend: {result.backend}",
        f"Source: {_display_path(source) if source is not None else 'none'}",
        f"Active table: {result.active_table or 'none'}",
        f"Last operation: {result.last_operation or 'none'}",
        f"Execution mode: {result.execution_mode or 'none'}",
        f"Lazy engine: {result.lazy_engine or 'none'}",
        f"Materialization: {materialization}",
        f"Last materialization reason: {reason}",
        f"Rows: {_row_count(result.row_count) if source is not None else 'none'}",
        f"Columns: {result.column_count if result.column_count is not None else 'none'}",
      )
    )

  if isinstance(result, SummarizeResult):
    summary_rows = (
      (
        row.variable,
        str(row.count),
        _format_number(row.mean),
        _format_number(row.std_dev),
        _format_number(row.minimum),
        _format_number(row.maximum),
      )
      for row in result.rows
    )
    return "\n".join(_table(("Variable", "Count", "Mean", "Std Dev", "Min", "Max"), summary_rows))

  if isinstance(result, TestResult):
    lines = []
    for index, constraint in enumerate(result.constraints, 1):
      lines.append(f" ({index:2d})  {constraint}")
    lines.append("")

    if result.is_chi2:
      lines.append(f"       chi2({result.df:3d})    =   {_format_number(result.statistic)}")
      lines.append(f"       Prob > chi2  =    {_format_number(result.p_value)}")
    else:
      df_resid = result.df_residual or 0
      f_stat = _format_number(result.statistic)
      lines.append(f"       F({result.df:3d}, {df_resid:4d}) =   {f_stat}")
      lines.append(f"       Prob > F     =    {_format_number(result.p_value)}")
    return "\n".join(lines)

  if isinstance(result, LincomResult):
    stat_header = "t" if result.df_residual is not None else "z"
    p_header = f"P>|{stat_header}|"
    level = result.ci_level
    ci_header = f"[{level:.0f}% Conf. Interval]"

    rows = (
      (
        result.label,
        _format_number(result.estimate),
        _format_number(result.standard_error),
        _format_number(result.statistic),
        _format_number(result.p_value),
        f"[{_format_number(result.ci_lower)}, {_format_number(result.ci_upper)}]",
      ),
    )
    table_lines = _table(
      ("Variable", "Coef", "Std Err", stat_header, p_header, ci_header),
      rows,
    )
    return "\n".join(table_lines)

  if isinstance(result, TtestResult):
    lines = []

    if result.is_paired:
      title = "Paired t test"
    elif result.by_variable is not None:
      var_type = "unequal" if result.is_welch else "equal"
      title = f"Two-sample t test with {var_type} variances"
    else:
      title = "One-sample t test"
    lines.append(title)

    col_name = "Group" if (result.by_variable is not None) else "Variable"
    headers = (col_name, "Obs", "Mean", "Std Err", "Std Dev", "Lower CI", "Upper CI")

    rows_data = []
    if result.is_paired:
      rows_data.append(_format_group_stats(result.group1_stats))
      if result.group2_stats is not None:
        rows_data.append(_format_group_stats(result.group2_stats))
      rows_data.append(_format_group_stats(result.difference_stats))
    elif result.by_variable is not None:
      rows_data.append(_format_group_stats(result.group1_stats))
      if result.group2_stats is not None:
        rows_data.append(_format_group_stats(result.group2_stats))
      if result.combined_stats is not None:
        rows_data.append(_format_group_stats(result.combined_stats))
      rows_data.append(_format_diff_row(result.difference_stats))
    else:
      rows_data.append(_format_group_stats(result.group1_stats))

    table_lines = _table(headers, rows_data)
    lines.extend(table_lines)

    t_str = _format_number(result.t_statistic)
    import math

    if result.is_welch:
      df_str = f"{result.df:.4f}"
    else:
      df_str = str(int(result.df)) if not math.isnan(result.df) else "."

    if result.is_paired:
      ha_desc = "mean(diff)"
    elif result.by_variable is not None:
      ha_desc = "diff"
    else:
      ha_desc = "mean"

    null_val = result.null_value if result.by_variable is None and not result.is_paired else 0.0
    ha_left = f"Ha: {ha_desc} < {null_val}"
    ha_two = f"Ha: {ha_desc} != {null_val}"
    ha_right = f"Ha: {ha_desc} > {null_val}"

    p_left_str = f"Pr(T < t) = {_format_number(result.p_left)}"
    p_two_str = f"Pr(|T| > |t|) = {_format_number(result.p_two)}"
    p_right_str = f"Pr(T > t) = {_format_number(result.p_right)}"

    test_header_line = f"    {ha_left:<26}  {ha_two:<26}  {ha_right:<26}"
    p_value_line = f" {p_left_str:<26}  {p_two_str:<26}  {p_right_str:<26}"

    lines.append("")
    if result.is_paired:
      lines.append(f"    mean(diff) = mean({result.varname1} - {result.varname2})")
      lines.append(f"Ho: mean(diff) = 0                                     df = {df_str}")
    elif result.by_variable is not None:
      g1_name = result.group1_stats.name
      g2_name = result.group2_stats.name if result.group2_stats is not None else ""
      lines.append(f"    diff = mean({g1_name}) - mean({g2_name})")
      lines.append(f"Ho: diff = 0                                           df = {df_str}")
    else:
      lines.append(f"    mean = mean({result.varname1})")
      ho_str = f"Ho: mean = {result.null_value}"
      lines.append(f"{ho_str:<54}df = {df_str}")

    lines.append(f"    t = {t_str}")
    lines.append("")
    lines.append(test_header_line)
    lines.append(p_value_line)

    return "\n".join(lines)

  if isinstance(result, CodebookResult):
    codebook_rows = (
      (
        row.variable,
        row.data_type,
        str(row.nonmissing),
        str(row.missing),
        str(row.distinct),
        ", ".join(_format_cell(value) for value in row.examples) or ".",
      )
      for row in result.rows
    )
    return "\n".join(
      _table(
        ("Variable", "Type", "Nonmissing", "Missing", "Distinct", "Examples"),
        codebook_rows,
      )
    )

  if isinstance(result, CountResult):
    return f"Rows: {result.row_count}"

  if isinstance(result, PreviewResult):
    preview_rows = (tuple(_format_cell(value) for value in row) for row in result.rows)
    return "\n".join(_table(result.columns, preview_rows))

  if isinstance(result, RegressionResult):
    header = [
      f"Model: regress {result.outcome} on {' '.join(result.predictors)}",
      f"Estimator: {result.estimator}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      f"Adj. R-squared: {_format_number(result.adjusted_r_squared)}",
      f"Root MSE: {_format_number(result.root_mse)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, LassoRegressionResult):
    header = [
      f"Model: lasso linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: lasso",
      f"Alpha: {_format_number(result.alpha)}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, PostlassoRegressionResult):
    selected = " ".join(result.selected_predictors) if result.selected_predictors else "(none)"
    header = [
      f"Model: postlasso linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: postlasso",
      f"Alpha: {_format_number(result.alpha)}",
      f"Selected Predictors: {selected}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      f"Adjusted R-squared: {_format_number(result.adjusted_r_squared)}",
      f"Root MSE: {_format_number(result.root_mse)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, RidgeRegressionResult):
    header = [
      f"Model: ridge linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: ridge",
      f"Alpha: {_format_number(result.alpha)}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, ElasticnetRegressionResult):
    header = [
      f"Model: elasticnet linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: elasticnet",
      f"Alpha: {_format_number(result.alpha)}",
      f"L1 Ratio: {_format_number(result.l1_ratio)}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, CvlassoRegressionResult):
    header = [
      f"Model: cvlasso linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: cvlasso",
      f"Folds: {result.cv}",
      f"Optimal Alpha: {_format_number(result.selected_alpha)}",
      f"Tuning Report: {result.report_path}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, CvridgeRegressionResult):
    header = [
      f"Model: cvridge linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: cvridge",
      f"Folds: {result.cv}",
      f"Optimal Alpha: {_format_number(result.selected_alpha)}",
      f"Tuning Report: {result.report_path}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, CvelasticnetRegressionResult):
    header = [
      f"Model: cvelasticnet linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: cvelasticnet",
      f"Folds: {result.cv}",
      f"Optimal Alpha: {_format_number(result.selected_alpha)}",
      f"Optimal L1 Ratio: {_format_number(result.selected_l1_ratio)}",
      f"Tuning Report: {result.report_path}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, BayesRegressionResult):
    header = [
      f"Model: bayes linear {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: bayesian_ridge",
      f"Iterations: {result.n_iter}",
      f"Noise Precision (Alpha): {_format_number(result.alpha)}",
      f"Prior Precision (Lambda): {_format_number(result.lambda_)}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, BayesMcmcResult):
    header = [
      f"Model: bayes: {result.command_name} {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: MCMC (bambi)",
      f"Chains: {result.chains}",
      f"Draws per chain: {result.draws}",
      f"Burn-in (Tune): {result.burnin}",
      f"Thinning: {result.thin}",
      f"Observations: {result.observation_count}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.mean),
        _format_number(estimate.sd),
        _format_number(estimate.mcse),
        f"[{_format_number(estimate.ci_lower)}, {_format_number(estimate.ci_upper)}]",
      )
      for estimate in result.estimates
    )
    body = _table(
      ("Variable", "Mean", "Std. Dev.", "MCSE", f"[{int(result.ci_level * 100)}% Cred. Interval]"),
      coefficient_rows,
    )
    return "\n".join([*header, *body])

  if isinstance(result, SpatialRegressionResult):
    if result.model_type == "lag":
      estimator_label = "Spatial Lag (SAR)"
    elif result.model_type == "error":
      estimator_label = "Spatial Error (SEM)"
    else:
      estimator_label = "Spatial Combo (SARAR)"
    if result.robust:
      estimator_label += " (Robust)"

    if result.coord_variables is not None:
      coord_str = " ".join(result.coord_variables)
      weights_line = f"Spatial Weights: KNN (k={result.knn}) from {coord_str}"
    else:
      contiguity_label = f", Contiguity: {result.contiguity}" if result.contiguity else ""
      weights_line = (
        f"Spatial Weights: File ({result.weights_file}) "
        f"with ID {result.id_variable}{contiguity_label}"
      )

    header = [
      f"Model: spregress {result.outcome} on {' '.join(result.predictors)}",
      f"Estimator: {estimator_label}",
      weights_line,
      f"Observations: {result.observation_count}",
      f"Pseudo R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, QregRegressionResult):
    header = [
      f"Model: qreg {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: qreg",
      f"Quantile: {_format_number(result.quantile)}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Pseudo R-squared: {_format_number(result.pseudo_r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, LogitRegressionResult):
    header = [
      f"Model: logit {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: logit",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Pseudo R-squared: {_format_number(result.pseudo_r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, ProbitRegressionResult):
    header = [
      f"Model: probit {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: probit",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Pseudo R-squared: {_format_number(result.pseudo_r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, TobitRegressionResult):
    limit_display = (
      f"ll={_format_number(result.lower_limit)}, ul={_format_number(result.upper_limit)}"
      if result.upper_limit is not None
      else f"ll={_format_number(result.lower_limit)}"
    )
    header = [
      f"Model: tobit {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: tobit",
      f"Limits: {limit_display}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, HeckmanRegressionResult):
    outcome_header = [
      (
        f"Model: heckman {result.outcome} on {' '.join(result.predictors)} "
        f"(selectdep={result.selection_dependent}; select={' '.join(result.selection_predictors)})"
      ),
      "Estimator: heckman",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      "",
      "Outcome Equation",
    ]
    outcome_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.outcome_coefficients
    )
    selection_header = [
      "",
      "Selection Equation",
    ]
    selection_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.selection_coefficients
    )
    return "\n".join(
      [
        *outcome_header,
        *_table(("Variable", "Coef", "Std Err", "z", "P>|z|"), outcome_rows),
        *selection_header,
        *_table(("Variable", "Coef", "Std Err", "z", "P>|z|"), selection_rows),
      ]
    )

  if isinstance(result, NlRegressionResult):
    header = [
      f"Model: nl {result.outcome} = {result.expression}",
      "Estimator: nl",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"RSS: {_format_number(result.residual_sum_of_squares)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Parameter", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, PoissonRegressionResult):
    header = [
      f"Model: poisson {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: poisson",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Log-likelihood: {_format_number(result.log_likelihood)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, NbregRegressionResult):
    header = [
      f"Model: nbreg {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: nbreg",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Log-likelihood: {_format_number(result.log_likelihood)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, ZipRegressionResult):
    header = [
      f"Model: zip {result.outcome} on {' '.join(result.predictors)}",
      f"Inflate: {' '.join(result.inflate_predictors)}",
      "Estimator: zip",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Log-likelihood: {_format_number(result.log_likelihood)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, ZinbRegressionResult):
    header = [
      f"Model: zinb {result.outcome} on {' '.join(result.predictors)}",
      f"Inflate: {' '.join(result.inflate_predictors)}",
      "Estimator: zinb",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Log-likelihood: {_format_number(result.log_likelihood)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, StregRegressionResult):
    header = [
      f"Model: streg {result.time_variable} on {' '.join(result.predictors)}",
      "Estimator: streg",
      f"Failure: {result.failure_variable}",
      f"Distribution: {result.distribution}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, IvRegressionResult):
    exogenous = " ".join(result.exogenous) if result.exogenous else "(none)"
    instruments = " ".join(result.instruments)
    header = [
      (
        f"Model: ivregress {result.estimator} {result.outcome} "
        f"on {exogenous} (endog={result.endogenous}; iv={instruments})"
      ),
      f"Estimator: {result.estimator}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, XtRegressionResult):
    header = [
      f"Model: xtreg {result.estimator} {result.outcome} on {' '.join(result.predictors)}",
      f"Estimator: {result.estimator}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"R-squared (within): {_format_number(result.r_squared_within)}",
      f"R-squared (between): {_format_number(result.r_squared_between)}",
      f"R-squared (overall): {_format_number(result.r_squared_overall)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, XtLogitRegressionResult):
    header = [
      f"Model: xtlogit {result.outcome} on {' '.join(result.predictors)}",
      "Estimator: xtlogit_fe",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "z", "P>|z|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, XtAbondRegressionResult):
    predictors = " ".join(result.predictors) if result.predictors else "(none)"
    header = [
      f"Model: xtabond {result.outcome} on {predictors}",
      "Estimator: xtabond_ar1_gmm",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Coefficients: {result.coefficient_count}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, DidRegressionResult):
    controls = " ".join(result.controls) if result.controls else "(none)"
    header = [
      (
        f"Model: did {result.outcome} on {controls} "
        f"(treat={result.treatment_variable}, post={result.post_variable})"
      ),
      "Estimator: did_twfe",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, DrDidRegressionResult):
    covariates = " ".join(result.covariates) if result.covariates else "(none)"
    header = [
      (
        f"Model: drdid {result.outcome} on {covariates} "
        f"(treat={result.treatment_variable}, post={result.post_variable})"
      ),
      f"Estimator: drdid_{result.method}",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      "",
    ]
    if result.notes:
      header.extend(result.notes)
      header.append("")
    drdid_rows = tuple(
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
        f"[{_format_number(result.lci)}, {_format_number(result.uci)}]",
      )
      for estimate in result.coefficients
    )
    body = _table(
      ("Variable", "Coef", "Std Err", "t", "P>|t|", "[95% Conf. Interval]"),
      drdid_rows,
    )
    return "\n".join([*header, *body])

  if isinstance(result, DmlRegressionResult):
    controls = " ".join(result.controls)
    header = [
      (f"Model: dml linear {result.outcome} on {controls} (treat={result.treatment_variable})"),
      "Estimator: dml",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"Folds: {result.folds}",
      f"Alpha: {result.alpha}",
      "",
    ]
    dml_rows = tuple(
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
        f"[{_format_number(result.lci)}, {_format_number(result.uci)}]",
      )
      for estimate in result.coefficients
    )
    body = _table(
      ("Variable", "Coef", "Std Err", "t", "P>|t|", "[95% Conf. Interval]"),
      dml_rows,
    )
    return "\n".join([*header, *body])

  if isinstance(result, CfRegressionResult):
    exogenous = " ".join(result.exogenous) if result.exogenous else "(none)"
    instruments = " ".join(result.instruments)
    header = [
      (
        f"Model: cfregress {result.outcome} on {exogenous} "
        f"(endog={result.endogenous}; iv={instruments})"
      ),
      "Estimator: control-function",
      f"Covariance: {result.covariance}",
      f"Observations: {result.observation_count}",
      f"R-squared: {_format_number(result.r_squared)}",
      "",
    ]
    coefficient_rows = (
      (
        estimate.name,
        _format_number(estimate.value),
        _format_number(estimate.standard_error),
        _format_number(estimate.statistic),
        _format_number(estimate.p_value),
      )
      for estimate in result.coefficients
    )
    body = _table(("Variable", "Coef", "Std Err", "t", "P>|t|"), coefficient_rows)
    return "\n".join([*header, *body])

  if isinstance(result, TransformResult):
    dataset = result.dataset
    overflow = f", overflow rows: {result.overflow_count}" if result.overflow_count else ""
    return (
      f"{result.message}: {_row_count(dataset.row_count)} rows, {dataset.column_count} columns"
      f"{overflow}"
    )

  if isinstance(result, PanelResult):
    if result.action == "clear":
      return "Panel cleared"
    if result.metadata is None:
      return "Panel: none"
    prefix = "Panel set" if result.action == "set" else "Panel"
    panel_header = (
      f"{prefix}: id={result.metadata.id_variable}, time={result.metadata.time_variable}"
    )
    if result.action != "report" or result.summary is None:
      return panel_header
    panel_summary = result.summary
    balanced = "yes" if panel_summary.is_balanced else "no"
    return "\n".join(
      (
        panel_header,
        f"Observations: {panel_summary.observation_count}",
        f"Entities: {panel_summary.entity_count}",
        f"Time periods: {panel_summary.time_count}",
        (
          "Obs per entity: "
          "min="
          f"{panel_summary.min_observations_per_entity}, max="
          f"{panel_summary.max_observations_per_entity}"
        ),
        f"Balanced: {balanced}",
      )
    )

  if isinstance(result, SqlCreateResult):
    dataset = result.dataset
    return (
      f"Created {result.table_name}: "
      f"{_row_count(dataset.row_count)} rows, {dataset.column_count} columns"
    )

  if isinstance(result, TableResult):
    table_rows = (tuple(_format_cell(value) for value in row) for row in result.rows)
    return "\n".join(_table(result.headers, table_rows))

  if isinstance(result, PlotResult):
    return f"Saved plot: {_display_path(result.path)}"

  if isinstance(result, SetResult):
    return f"Set {result.name}: {result.value}"

  if isinstance(result, SaveResult):
    dataset = result.dataset
    return (
      f"Saved: {_display_path(result.path)} "
      f"({_row_count(dataset.row_count)} rows, {dataset.column_count} columns)"
    )

  if isinstance(result, ExportResult):
    dataset = result.dataset
    return (
      f"Exported: {_display_path(result.path)} "
      f"({_row_count(dataset.row_count)} rows, {dataset.column_count} columns)"
    )

  raise TypeError(f"Unsupported result: {type(result).__name__}")


def format_result_json(result: Result) -> str:
  """Serialize one successful result as a deterministic machine-readable envelope."""
  raw_data = TypeAdapter(type(result)).dump_python(result, mode="python")
  data = _json_safe_value(raw_data)
  envelope = {
    "schema_version": 1,
    "result_type": _result_type_label(result),
    "data": data,
  }
  return json.dumps(
    envelope,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
  )


def format_error_json(error: TabDatError) -> str:
  """Serialize one user-facing failure as a deterministic machine-readable envelope."""
  error_data: dict[str, object] = {
    "type": _error_type_label(error),
    "message": _machine_error_message(error),
  }
  if isinstance(error, ScriptError):
    error_data["path"] = str(error.path)
    error_data["line"] = error.line
  envelope = {"schema_version": 1, "error": error_data}
  return json.dumps(
    envelope,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
  )


def _result_type_label(result: Result) -> str:
  try:
    return RESULT_TYPE_LABELS[type(result)]
  except KeyError as exc:
    raise TypeError(f"Unsupported result: {type(result).__name__}") from exc


def _error_type_label(error: TabDatError) -> str:
  try:
    return ERROR_TYPE_LABELS[type(error)]
  except KeyError as exc:
    raise TypeError(f"Unsupported error: {type(error).__name__}") from exc


def _machine_error_message(error: TabDatError) -> str:
  message = error.message if isinstance(error, ScriptError) else str(error)
  if error.__cause__ is not None and not isinstance(error.__cause__, TabDatError):
    return message.split(": ", maxsplit=1)[0]
  return message


def _json_safe_value(value: object) -> object:
  if value is None or isinstance(value, (str, int, bool)):
    return value
  if isinstance(value, float):
    return value if math.isfinite(value) else None
  if isinstance(value, Decimal):
    return format(value, "f")
  if isinstance(value, Path):
    return str(value)
  if isinstance(value, (bytes, bytearray, memoryview)):
    encoded = base64.b64encode(bytes(value)).decode("ascii")
    return f"base64:{encoded}"
  if isinstance(value, (datetime, date, time)):
    return value.isoformat()
  if isinstance(value, Enum):
    return _json_safe_value(value.value)
  if isinstance(value, dict):
    return {str(key): _json_safe_value(item) for key, item in value.items()}
  if isinstance(value, (tuple, list)):
    return [_json_safe_value(item) for item in value]
  raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def _row_count(row_count: int | None) -> str:
  if row_count is None:
    return "unknown"
  return str(row_count)


def _table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
  materialized = list(rows)
  widths = [
    max(len(value) for value in column) for column in zip(headers, *materialized, strict=False)
  ]
  lines = [_format_row(headers, widths)]
  lines.extend(_format_row(row, widths) for row in materialized)
  return lines


def _format_row(values: Sequence[str], widths: Sequence[int]) -> str:
  return "  ".join(value.ljust(width) for value, width in zip(values, widths, strict=True))


def _format_number(value: float | int | None) -> str:
  if value is None:
    return "."
  if isinstance(value, int):
    return str(value)
  return f"{value:.6g}"


def _format_cell(value: object) -> str:
  if value is None:
    return "."
  if isinstance(value, float):
    return _format_number(value)
  return str(value)


def _display_path(path: Path | str) -> str:
  if isinstance(path, str):
    return path
  try:
    return str(path.relative_to(Path.cwd()))
  except ValueError:
    return str(path)


def _format_group_stats(stats: TtestGroupStats) -> tuple[str, str, str, str, str, str, str]:
  return (
    stats.name,
    str(stats.obs),
    _format_number(stats.mean),
    _format_number(stats.std_err),
    _format_number(stats.std_dev),
    _format_number(stats.ci_lower),
    _format_number(stats.ci_upper),
  )


def _format_diff_row(stats: TtestGroupStats) -> tuple[str, str, str, str, str, str, str]:
  return (
    stats.name,
    "",
    _format_number(stats.mean),
    _format_number(stats.std_err),
    "",
    _format_number(stats.ci_lower),
    _format_number(stats.ci_upper),
  )

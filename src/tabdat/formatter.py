"""Terminal formatting for structured command results."""

from collections.abc import Iterable, Sequence
from pathlib import Path

from tabdat.models import (
  ActivateResult,
  CfRegressionResult,
  CodebookResult,
  CountResult,
  DescribeResult,
  ExportResult,
  IvRegressionResult,
  LoadResult,
  LogitRegressionResult,
  PanelResult,
  PlotResult,
  PreviewResult,
  RegressionResult,
  Result,
  SaveResult,
  SetResult,
  SqlCreateResult,
  SummarizeResult,
  TableResult,
  TransformResult,
  XtRegressionResult,
)


def format_result(result: Result) -> str:
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
    return f"{result.message}: {_row_count(dataset.row_count)} rows, {dataset.column_count} columns"

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

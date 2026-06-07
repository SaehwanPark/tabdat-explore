"""Terminal formatting for structured command results."""

from collections.abc import Iterable, Sequence
from pathlib import Path

from tabdat.models import (
  ActivateResult,
  BayesRegressionResult,
  CfRegressionResult,
  CodebookResult,
  CountResult,
  CvelasticnetRegressionResult,
  CvlassoRegressionResult,
  CvridgeRegressionResult,
  DescribeResult,
  DidRegressionResult,
  DrDidRegressionResult,
  ElasticnetRegressionResult,
  ExportResult,
  HeckmanRegressionResult,
  IvRegressionResult,
  LassoRegressionResult,
  LoadResult,
  LogitRegressionResult,
  NbregRegressionResult,
  NlRegressionResult,
  PanelResult,
  PlotResult,
  PoissonRegressionResult,
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
  StregRegressionResult,
  SummarizeResult,
  TableResult,
  TobitRegressionResult,
  TransformResult,
  XtAbondRegressionResult,
  XtLogitRegressionResult,
  XtRegressionResult,
  ZinbRegressionResult,
  ZipRegressionResult,
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

  if isinstance(result, SpatialRegressionResult):
    estimator_label = "Spatial Lag (SAR)" if result.model_type == "lag" else "Spatial Error (SEM)"
    if result.robust:
      estimator_label += " (Robust)"

    header = [
      f"Model: spregress {result.outcome} on {' '.join(result.predictors)}",
      f"Estimator: {estimator_label}",
      f"Spatial Weights: KNN (k={result.knn}) from {' '.join(result.coord_variables)}",
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

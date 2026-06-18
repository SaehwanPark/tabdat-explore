"""Structured command and result models for the TabDat pipeline."""

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from tabdat.estimation import CoefficientEstimate

_MODEL_CONFIG = ConfigDict(strict=True)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class IdentifierExpression:
  name: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class NumberExpression:
  value: int | float


@dataclass(frozen=True, config=_MODEL_CONFIG)
class StringExpression:
  value: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class UnaryExpression:
  operator: Literal["-"]
  operand: "Expression"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BinaryExpression:
  left: "Expression"
  operator: Literal["+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">="]
  right: "Expression"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class FunctionCallExpression:
  name: str
  arguments: tuple["Expression", ...]


Expression = (
  IdentifierExpression
  | NumberExpression
  | StringExpression
  | UnaryExpression
  | BinaryExpression
  | FunctionCallExpression
)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CommandOption:
  name: str
  value: str | int | float | bool | tuple[str, ...] = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class UseCommand:
  path: Path | str
  execution_mode: Literal["eager", "lazy"] = "eager"
  lazy_engine: Literal["duckdb", "polars"] | None = None
  delimiter: str | None = None
  has_header: bool | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DescribeCommand:
  pass


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SummarizeCommand:
  variables: tuple[str, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CodebookCommand:
  variables: tuple[str, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CountCommand:
  pass


@dataclass(frozen=True, config=_MODEL_CONFIG)
class HeadCommand:
  limit: int = 5


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TailCommand:
  limit: int = 5


@dataclass(frozen=True, config=_MODEL_CONFIG)
class KeepCommand:
  variables: tuple[str, ...] = ()
  condition: Expression | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DropCommand:
  variables: tuple[str, ...] = ()
  condition: Expression | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SelectCommand:
  variables: tuple[str, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RenameCommand:
  old_name: str
  new_name: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class GenerateCommand:
  variable: str
  expression: Expression


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ReplaceCommand:
  variable: str
  expression: Expression
  condition: Expression | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TabulateCommand:
  row_variables: tuple[str, ...]
  column_variables: tuple[str, ...] = ()
  condition: Expression | None = None
  value_variable: str | None = None
  statistic: Literal["count", "mean", "sum", "min", "max"] | None = None
  row_percent: bool = False
  column_percent: bool = False
  include_missing: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CollapseCommand:
  statistic: Literal["count", "mean", "sum", "min", "max"]
  variables: tuple[str, ...]
  groups: tuple[str, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class JoinCommand:
  table_name: str
  keys: tuple[str, ...]
  how: Literal["inner", "left"] = "inner"
  suffix: str = "_right"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class AppendCommand:
  table_name: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ReshapeCommand:
  direction: Literal["long", "wide"]
  variables: tuple[str, ...]
  identifiers: tuple[str, ...]
  j_variable: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PanelCommand:
  action: Literal["report", "set", "clear"]
  id_variable: str | None = None
  time_variable: str | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SqlCommand:
  query: str
  into: str | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class HistogramCommand:
  variable: str
  bins: int | None = None
  saving: Path | None = None
  open_artifact: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ScatterCommand:
  y_variable: str
  x_variable: str
  saving: Path | None = None
  open_artifact: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BarCommand:
  variable: str
  saving: Path | None = None
  include_missing: bool = False
  open_artifact: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BayesPlotCommand:
  kind: Literal["trace", "density", "autocorrelation"]
  saving: Path | None = None
  open_artifact: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ByCommand:
  groups: tuple[str, ...]
  command: "Command"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BayesPrefixCommand:
  command: "Command"
  draws: int | None = None
  burnin: int | None = None
  chains: int | None = None
  thin: int | None = None
  seed: int | None = None
  priors: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ExitCommand:
  pass


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RunCommand:
  path: Path


@dataclass(frozen=True, config=_MODEL_CONFIG)
class HelpCommand:
  topic: str | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SetCommand:
  name: Literal["graph_format", "artifact_dir", "graph_open"]
  value: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SaveCommand:
  path: Path
  replace: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ExportCommand:
  path: Path
  replace: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RegressCommand:
  outcome: str
  predictors: tuple[str, ...]
  estimator: Literal["ols", "wls", "gls"] = "ols"
  weight_variable: str | None = None
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LassoCommand:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float = 1.0
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PostlassoCommand:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float = 1.0
  robust: bool = False
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RidgeCommand:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float = 1.0
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ElasticnetCommand:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float = 1.0
  l1_ratio: float = 0.5
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CvlassoCommand:
  outcome: str
  predictors: tuple[str, ...]
  cv: int = 5
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CvridgeCommand:
  outcome: str
  predictors: tuple[str, ...]
  cv: int = 5
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CvelasticnetCommand:
  outcome: str
  predictors: tuple[str, ...]
  cv: int = 5
  l1_ratio: float | tuple[float, ...] = (0.1, 0.5, 0.7, 0.9, 0.95, 0.99, 1.0)
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BayesCommand:
  outcome: str
  predictors: tuple[str, ...]
  n_iter: int = 300
  tol: float = 0.001
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SpregressCommand:
  outcome: str
  predictors: tuple[str, ...]
  model_type: Literal["lag", "error", "sarar"]
  coord_variables: tuple[str, str] | None = None
  knn: int | None = None
  weights_file: str | None = None
  id_variable: str | None = None
  contiguity: Literal["queen", "rook"] | None = None
  robust: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class QregCommand:
  outcome: str
  predictors: tuple[str, ...]
  quantile: float = 0.5
  robust: bool = False
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LogitCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ProbitCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PredictCommand:
  target_variable: str
  kind: Literal["xb", "residuals", "pr", "spatial_lag", "posterior_predictive"] = "xb"
  interval: bool = False
  level: float = 95.0


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TobitCommand:
  outcome: str
  predictors: tuple[str, ...]
  lower_limit: float
  upper_limit: float | None = None
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class HeckmanCommand:
  outcome: str
  predictors: tuple[str, ...]
  selection_dependent: str
  selection_predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class NlCommand:
  outcome: str
  expression: Expression
  parameter_names: tuple[str, ...]
  start_values: tuple[float, ...]
  robust: bool = False
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PoissonCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class NbregCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ZipCommand:
  outcome: str
  predictors: tuple[str, ...]
  inflate_predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ZinbCommand:
  outcome: str
  predictors: tuple[str, ...]
  inflate_predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class StregCommand:
  time_variable: str
  predictors: tuple[str, ...]
  failure_variable: str
  distribution: Literal["weibull", "exponential"]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class EstatCommand:
  subcommand: Literal[
    "residuals",
    "ovtest",
    "vif",
    "firststage",
    "overid",
    "hausman",
    "endogenous",
    "margins",
    "gof",
    "did",
    "drdid",
    "dml",
    "bayes",
    "spatial",
  ]
  coord_variables: tuple[str, str] | None = None
  knn: int | None = None
  weights_file: str | None = None
  id_variable: str | None = None
  contiguity: Literal["queen", "rook"] | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class IvRegressCommand:
  outcome: str
  exogenous: tuple[str, ...]
  endogenous: str
  instruments: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True
  estimator: Literal["2sls", "gmm"] = "2sls"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtRegCommand:
  outcome: str
  predictors: tuple[str, ...]
  estimator: Literal["fe", "re"]
  robust: bool = False
  cluster_variable: str | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtDataCommand:
  variables: tuple[str, ...]
  transform: Literal["within", "between"]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtLogitCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtAbondCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False
  lag_depth: int = 1
  instrument_lag_start: int = 2


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LowessCommand:
  outcome: str
  predictor: str
  target_variable: str
  bandwidth: float = 0.6666666666666666


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DidCommand:
  outcome: str
  controls: tuple[str, ...]
  treatment_variable: str
  post_variable: str
  robust: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DrDidCommand:
  outcome: str
  covariates: tuple[str, ...]
  treatment_variable: str
  post_variable: str
  method: Literal["or", "ipw", "aipw"] = "aipw"
  robust: bool = False
  bootstrap: int | None = None
  seed: int | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DmlCommand:
  outcome: str
  controls: tuple[str, ...]
  treatment_variable: str
  folds: int = 5
  alpha: float = 1.0
  robust: bool = False
  seed: int | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CfRegressCommand:
  outcome: str
  exogenous: tuple[str, ...]
  endogenous: str
  instruments: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TestCommand:
  __test__ = False
  constraints: tuple[Expression, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LincomCommand:
  expression: Expression


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TtestCommand:
  varname1: str
  varname2: str | None = None
  value: float | None = None
  by_variable: str | None = None
  welch: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RecodeRange:
  start: float | Literal["min"]
  end: float | Literal["max"]


RecodeInput = float | int | str | RecodeRange | Literal["missing", "nonmissing", "else"]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RecodeRule:
  inputs: tuple[RecodeInput, ...]
  output: float | int | str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RecodeCommand:
  variables: tuple[str, ...]
  rules: tuple[RecodeRule, ...]
  generate_variables: tuple[str, ...] | None = None
  replace: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ParsedCommand:
  name: str
  arguments: tuple[str, ...] = ()
  condition: Expression | None = None
  options: tuple[CommandOption, ...] = ()
  expression: Expression | None = None


Command = (
  UseCommand
  | RecodeCommand
  | DescribeCommand
  | SummarizeCommand
  | CodebookCommand
  | CountCommand
  | HeadCommand
  | TailCommand
  | KeepCommand
  | DropCommand
  | SelectCommand
  | RenameCommand
  | GenerateCommand
  | ReplaceCommand
  | TabulateCommand
  | CollapseCommand
  | JoinCommand
  | AppendCommand
  | ReshapeCommand
  | PanelCommand
  | SqlCommand
  | HistogramCommand
  | ScatterCommand
  | BarCommand
  | BayesPlotCommand
  | ByCommand
  | ExitCommand
  | RunCommand
  | HelpCommand
  | SetCommand
  | SaveCommand
  | ExportCommand
  | RegressCommand
  | LassoCommand
  | PostlassoCommand
  | RidgeCommand
  | ElasticnetCommand
  | CvlassoCommand
  | CvridgeCommand
  | CvelasticnetCommand
  | BayesCommand
  | SpregressCommand
  | QregCommand
  | LogitCommand
  | ProbitCommand
  | TobitCommand
  | HeckmanCommand
  | NlCommand
  | PoissonCommand
  | NbregCommand
  | ZipCommand
  | ZinbCommand
  | StregCommand
  | PredictCommand
  | EstatCommand
  | IvRegressCommand
  | XtRegCommand
  | XtDataCommand
  | XtLogitCommand
  | XtAbondCommand
  | LowessCommand
  | DidCommand
  | DrDidCommand
  | DmlCommand
  | CfRegressCommand
  | BayesPrefixCommand
  | TestCommand
  | LincomCommand
  | TtestCommand
  | ParsedCommand
)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ColumnInfo:
  name: str
  data_type: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PanelMetadata:
  id_variable: str
  time_variable: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PanelStructureSummary:
  observation_count: int
  entity_count: int
  time_count: int
  min_observations_per_entity: int
  max_observations_per_entity: int

  @property
  def is_balanced(self) -> bool:
    return self.min_observations_per_entity == self.max_observations_per_entity


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DatasetInfo:
  path: Path | str
  row_count: int | None
  columns: tuple[ColumnInfo, ...]
  execution_mode: Literal["eager", "lazy"] = "eager"
  lazy_engine: Literal["duckdb", "polars"] | None = None
  panel_metadata: PanelMetadata | None = None

  @property
  def column_count(self) -> int:
    return len(self.columns)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LoadResult:
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ActivateResult:
  table_name: str
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DescribeResult:
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SummaryRow:
  variable: str
  count: int
  mean: float | None
  std_dev: float | None
  minimum: float | int | None
  maximum: float | int | None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SummarizeResult:
  rows: tuple[SummaryRow, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CodebookRow:
  variable: str
  data_type: str
  nonmissing: int
  missing: int
  distinct: int
  examples: tuple[object, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CodebookResult:
  rows: tuple[CodebookRow, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CountResult:
  row_count: int


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PreviewResult:
  columns: tuple[str, ...]
  rows: tuple[tuple[object, ...], ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TransformResult:
  message: str
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  estimator: Literal["ols", "wls", "gls"]
  covariance: str
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  adjusted_r_squared: float | None
  root_mse: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LassoRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PostlassoRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  selected_predictors: tuple[str, ...]
  alpha: float
  covariance: Literal["nonrobust", "robust"]
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  adjusted_r_squared: float | None
  root_mse: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RidgeRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ElasticnetRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  alpha: float
  l1_ratio: float
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CvlassoRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  selected_alpha: float
  cv: int
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]
  report_path: Path


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CvridgeRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  selected_alpha: float
  cv: int
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]
  report_path: Path


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CvelasticnetRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  selected_alpha: float
  selected_l1_ratio: float
  cv: int
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]
  report_path: Path


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BayesRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  n_iter: int
  alpha: float
  lambda_: float
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BayesMcmcEstimate:
  name: str
  mean: float
  sd: float
  mcse: float
  ci_lower: float
  ci_upper: float


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BayesMcmcResult:
  outcome: str
  predictors: tuple[str, ...]
  command_name: str
  draws: int
  burnin: int
  chains: int
  thin: int
  observation_count: int
  estimates: tuple[BayesMcmcEstimate, ...]
  ci_level: float = 0.95


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SpatialRegressionResult:
  outcome: str
  predictors: tuple[str, ...]
  model_type: Literal["lag", "error", "sarar"]
  robust: bool
  observation_count: int
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]
  spatial_coefficient: float
  spatial_coefficient_name: str
  coord_variables: tuple[str, str] | None = None
  knn: int | None = None
  weights_file: str | None = None
  id_variable: str | None = None
  contiguity: Literal["queen", "rook"] | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class QregRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  quantile: float
  observation_count: int
  include_intercept: bool
  pseudo_r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LogitRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  pseudo_r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ProbitRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  pseudo_r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TobitRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  lower_limit: float
  upper_limit: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class HeckmanRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  selection_dependent: str
  selection_predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  outcome_coefficients: tuple[CoefficientEstimate, ...]
  selection_coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class NlRegressionResult:
  covariance: str
  outcome: str
  expression: str
  parameter_names: tuple[str, ...]
  observation_count: int
  residual_sum_of_squares: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PoissonRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  log_likelihood: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class NbregRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  log_likelihood: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ZipRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  inflate_predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  log_likelihood: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ZinbRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  inflate_predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  log_likelihood: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class StregRegressionResult:
  covariance: str
  time_variable: str
  predictors: tuple[str, ...]
  failure_variable: str
  distribution: Literal["weibull", "exponential"]
  observation_count: int
  include_intercept: bool
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class IvRegressionResult:
  estimator: Literal["2sls", "gmm"]
  covariance: str
  outcome: str
  exogenous: tuple[str, ...]
  endogenous: str
  instruments: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtRegressionResult:
  estimator: Literal["fe", "re"]
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  r_squared_within: float | None
  r_squared_between: float | None
  r_squared_overall: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtLogitRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DidRegressionResult:
  covariance: str
  outcome: str
  controls: tuple[str, ...]
  treatment_variable: str
  post_variable: str
  observation_count: int
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DrDidRegressionResult:
  covariance: str
  outcome: str
  covariates: tuple[str, ...]
  treatment_variable: str
  post_variable: str
  method: str
  observation_count: int
  coefficients: tuple[CoefficientEstimate, ...]
  lci: float
  uci: float
  notes: tuple[str, ...] = ()


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DmlRegressionResult:
  covariance: Literal["nonrobust", "robust"]
  outcome: str
  controls: tuple[str, ...]
  treatment_variable: str
  folds: int
  alpha: float
  observation_count: int
  coefficients: tuple[CoefficientEstimate, ...]
  lci: float
  uci: float


@dataclass(frozen=True, config=_MODEL_CONFIG)
class XtAbondRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  coefficient_count: int
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CfRegressionResult:
  covariance: str
  outcome: str
  exogenous: tuple[str, ...]
  endogenous: str
  instruments: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  r_squared: float | None
  coefficients: tuple[CoefficientEstimate, ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PanelResult:
  action: Literal["report", "set", "clear"]
  metadata: PanelMetadata | None = None
  summary: PanelStructureSummary | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SqlCreateResult:
  table_name: str
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TableResult:
  headers: tuple[str, ...]
  rows: tuple[tuple[object, ...], ...]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PlotResult:
  path: Path
  should_open: bool


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SetResult:
  name: str
  value: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class SaveResult:
  path: Path
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ExportResult:
  path: Path
  dataset: DatasetInfo


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TestResult:
  __test__ = False
  constraints: tuple[str, ...]
  statistic: float
  p_value: float
  df: int
  df_residual: int | None = None
  is_chi2: bool = False


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LincomResult:
  label: str
  estimate: float
  standard_error: float
  statistic: float
  p_value: float
  ci_lower: float
  ci_upper: float
  ci_level: float = 95.0
  df_residual: int | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TtestGroupStats:
  name: str
  obs: int
  mean: float
  std_err: float
  std_dev: float
  ci_lower: float
  ci_upper: float


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TtestResult:
  varname1: str
  varname2: str | None
  by_variable: str | None
  is_paired: bool
  is_welch: bool
  null_value: float
  group1_stats: TtestGroupStats
  group2_stats: TtestGroupStats | None
  combined_stats: TtestGroupStats | None
  difference_stats: TtestGroupStats
  t_statistic: float
  df: float
  p_left: float
  p_two: float
  p_right: float


Result = (
  LoadResult
  | ActivateResult
  | DescribeResult
  | SummarizeResult
  | CodebookResult
  | CountResult
  | PreviewResult
  | TransformResult
  | RegressionResult
  | LassoRegressionResult
  | PostlassoRegressionResult
  | RidgeRegressionResult
  | ElasticnetRegressionResult
  | CvlassoRegressionResult
  | CvridgeRegressionResult
  | CvelasticnetRegressionResult
  | BayesRegressionResult
  | SpatialRegressionResult
  | QregRegressionResult
  | LogitRegressionResult
  | ProbitRegressionResult
  | TobitRegressionResult
  | HeckmanRegressionResult
  | NlRegressionResult
  | PoissonRegressionResult
  | NbregRegressionResult
  | ZipRegressionResult
  | ZinbRegressionResult
  | StregRegressionResult
  | IvRegressionResult
  | XtRegressionResult
  | XtLogitRegressionResult
  | XtAbondRegressionResult
  | DidRegressionResult
  | DrDidRegressionResult
  | DmlRegressionResult
  | CfRegressionResult
  | PanelResult
  | SqlCreateResult
  | TableResult
  | PlotResult
  | SetResult
  | SaveResult
  | ExportResult
  | BayesMcmcResult
  | TestResult
  | LincomResult
  | TtestResult
)

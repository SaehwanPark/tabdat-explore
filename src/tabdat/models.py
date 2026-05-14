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
  variables: tuple[str, ...]
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
class ByCommand:
  groups: tuple[str, ...]
  command: "Command"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ExitCommand:
  pass


@dataclass(frozen=True, config=_MODEL_CONFIG)
class RunCommand:
  path: Path


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
class LogitCommand:
  outcome: str
  predictors: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class PredictCommand:
  target_variable: str
  kind: Literal["xb", "residuals"] = "xb"


@dataclass(frozen=True, config=_MODEL_CONFIG)
class EstatCommand:
  subcommand: Literal["residuals", "ovtest", "vif", "firststage", "overid", "hausman", "endogenous"]


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
class CfRegressCommand:
  outcome: str
  exogenous: tuple[str, ...]
  endogenous: str
  instruments: tuple[str, ...]
  robust: bool = False
  cluster_variable: str | None = None
  include_intercept: bool = True


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ParsedCommand:
  name: str
  arguments: tuple[str, ...] = ()
  condition: Expression | None = None
  options: tuple[CommandOption, ...] = ()
  expression: Expression | None = None


Command = (
  UseCommand
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
  | ByCommand
  | ExitCommand
  | RunCommand
  | SetCommand
  | SaveCommand
  | ExportCommand
  | RegressCommand
  | LogitCommand
  | PredictCommand
  | EstatCommand
  | IvRegressCommand
  | XtRegCommand
  | XtDataCommand
  | CfRegressCommand
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
class LogitRegressionResult:
  covariance: str
  outcome: str
  predictors: tuple[str, ...]
  observation_count: int
  include_intercept: bool
  pseudo_r_squared: float | None
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
  | LogitRegressionResult
  | IvRegressionResult
  | XtRegressionResult
  | CfRegressionResult
  | PanelResult
  | SqlCreateResult
  | TableResult
  | PlotResult
  | SetResult
  | SaveResult
  | ExportResult
)

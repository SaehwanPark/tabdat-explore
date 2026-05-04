"""Structured command and result models for the TabDat pipeline."""

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

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
  path: Path
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
  | SqlCommand
  | HistogramCommand
  | ScatterCommand
  | BarCommand
  | ByCommand
  | ExitCommand
  | ParsedCommand
)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ColumnInfo:
  name: str
  data_type: str


@dataclass(frozen=True, config=_MODEL_CONFIG)
class DatasetInfo:
  path: Path
  row_count: int
  columns: tuple[ColumnInfo, ...]
  execution_mode: Literal["eager", "lazy"] = "eager"
  lazy_engine: Literal["duckdb", "polars"] | None = None

  @property
  def column_count(self) -> int:
    return len(self.columns)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LoadResult:
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


Result = (
  LoadResult
  | DescribeResult
  | SummarizeResult
  | CodebookResult
  | CountResult
  | PreviewResult
  | TransformResult
  | SqlCreateResult
  | TableResult
  | PlotResult
)

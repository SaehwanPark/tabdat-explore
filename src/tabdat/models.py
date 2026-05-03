"""Structured command and result models for the TabDat pipeline."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class IdentifierExpression:
  name: str


@dataclass(frozen=True)
class NumberExpression:
  value: int | float


@dataclass(frozen=True)
class StringExpression:
  value: str


@dataclass(frozen=True)
class UnaryExpression:
  operator: Literal["-"]
  operand: "Expression"


@dataclass(frozen=True)
class BinaryExpression:
  left: "Expression"
  operator: Literal["+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">="]
  right: "Expression"


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class CommandOption:
  name: str
  value: str | int | float | bool | tuple[str, ...] = True


@dataclass(frozen=True)
class UseCommand:
  path: Path


@dataclass(frozen=True)
class DescribeCommand:
  pass


@dataclass(frozen=True)
class SummarizeCommand:
  variables: tuple[str, ...]


@dataclass(frozen=True)
class CodebookCommand:
  variables: tuple[str, ...]


@dataclass(frozen=True)
class CountCommand:
  pass


@dataclass(frozen=True)
class HeadCommand:
  limit: int = 5


@dataclass(frozen=True)
class TailCommand:
  limit: int = 5


@dataclass(frozen=True)
class KeepCommand:
  variables: tuple[str, ...] = ()
  condition: Expression | None = None


@dataclass(frozen=True)
class DropCommand:
  variables: tuple[str, ...] = ()
  condition: Expression | None = None


@dataclass(frozen=True)
class SelectCommand:
  variables: tuple[str, ...]


@dataclass(frozen=True)
class RenameCommand:
  old_name: str
  new_name: str


@dataclass(frozen=True)
class GenerateCommand:
  variable: str
  expression: Expression


@dataclass(frozen=True)
class ReplaceCommand:
  variable: str
  expression: Expression
  condition: Expression | None = None


@dataclass(frozen=True)
class TabulateCommand:
  variables: tuple[str, ...]
  row_percent: bool = False
  column_percent: bool = False
  include_missing: bool = False


@dataclass(frozen=True)
class CollapseCommand:
  statistic: Literal["count", "mean", "sum", "min", "max"]
  variables: tuple[str, ...]
  groups: tuple[str, ...]


@dataclass(frozen=True)
class SqlCommand:
  query: str
  into: str | None = None


@dataclass(frozen=True)
class ByCommand:
  groups: tuple[str, ...]
  command: "Command"


@dataclass(frozen=True)
class ExitCommand:
  pass


@dataclass(frozen=True)
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
  | ByCommand
  | ExitCommand
  | ParsedCommand
)


@dataclass(frozen=True)
class ColumnInfo:
  name: str
  data_type: str


@dataclass(frozen=True)
class DatasetInfo:
  path: Path
  row_count: int
  columns: tuple[ColumnInfo, ...]

  @property
  def column_count(self) -> int:
    return len(self.columns)


@dataclass(frozen=True)
class LoadResult:
  dataset: DatasetInfo


@dataclass(frozen=True)
class DescribeResult:
  dataset: DatasetInfo


@dataclass(frozen=True)
class SummaryRow:
  variable: str
  count: int
  mean: float | None
  std_dev: float | None
  minimum: float | int | None
  maximum: float | int | None


@dataclass(frozen=True)
class SummarizeResult:
  rows: tuple[SummaryRow, ...]


@dataclass(frozen=True)
class CodebookRow:
  variable: str
  data_type: str
  nonmissing: int
  missing: int
  distinct: int
  examples: tuple[object, ...]


@dataclass(frozen=True)
class CodebookResult:
  rows: tuple[CodebookRow, ...]


@dataclass(frozen=True)
class CountResult:
  row_count: int


@dataclass(frozen=True)
class PreviewResult:
  columns: tuple[str, ...]
  rows: tuple[tuple[object, ...], ...]


@dataclass(frozen=True)
class TransformResult:
  message: str
  dataset: DatasetInfo


@dataclass(frozen=True)
class SqlCreateResult:
  table_name: str
  dataset: DatasetInfo


@dataclass(frozen=True)
class TableResult:
  headers: tuple[str, ...]
  rows: tuple[tuple[object, ...], ...]


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
)

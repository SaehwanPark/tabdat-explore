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
  value: str | int | float | bool = True


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
class ExitCommand:
  pass


@dataclass(frozen=True)
class ParsedCommand:
  name: str
  arguments: tuple[str, ...] = ()
  condition: Expression | None = None
  options: tuple[CommandOption, ...] = ()
  expression: Expression | None = None


Command = UseCommand | DescribeCommand | SummarizeCommand | ExitCommand | ParsedCommand


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


Result = LoadResult | DescribeResult | SummarizeResult

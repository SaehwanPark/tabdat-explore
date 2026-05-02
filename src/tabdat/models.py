"""Structured command and result models for the Phase 1 pipeline."""

from dataclasses import dataclass
from pathlib import Path


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


Command = UseCommand | DescribeCommand | SummarizeCommand | ExitCommand


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

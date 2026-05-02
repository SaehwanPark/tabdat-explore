"""Command executor and session state."""

from dataclasses import dataclass

from tabdat.backend import DuckDBBackend
from tabdat.errors import ExecutionError
from tabdat.models import (
  Command,
  DatasetInfo,
  DescribeCommand,
  DescribeResult,
  ExitCommand,
  LoadResult,
  Result,
  SummarizeCommand,
  SummarizeResult,
  UseCommand,
)


@dataclass
class SessionState:
  active_dataset: DatasetInfo | None = None


class Executor:
  def __init__(self, backend: DuckDBBackend | None = None) -> None:
    self.backend = backend or DuckDBBackend()
    self.state = SessionState()

  def close(self) -> None:
    self.backend.close()

  def execute(self, command: Command) -> Result | None:
    if isinstance(command, UseCommand):
      dataset = self.backend.inspect_parquet(command.path)
      self.state.active_dataset = dataset
      return LoadResult(dataset=dataset)

    if isinstance(command, DescribeCommand):
      dataset = self._require_active_dataset("describe")
      return DescribeResult(dataset=dataset)

    if isinstance(command, SummarizeCommand):
      dataset = self._require_active_dataset("summarize")
      rows = self.backend.summarize(dataset, command.variables)
      return SummarizeResult(rows=rows)

    if isinstance(command, ExitCommand):
      return None

    raise ExecutionError("unsupported command")

  def _require_active_dataset(self, command_name: str) -> DatasetInfo:
    if self.state.active_dataset is None:
      raise ExecutionError(f"{command_name} requires an active dataset; run use <path> first")
    return self.state.active_dataset

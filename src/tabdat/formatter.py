"""Terminal formatting for structured command results."""

from collections.abc import Iterable, Sequence
from pathlib import Path

from tabdat.models import (
  CodebookResult,
  CountResult,
  DescribeResult,
  LoadResult,
  PlotResult,
  PreviewResult,
  Result,
  SqlCreateResult,
  SummarizeResult,
  TableResult,
  TransformResult,
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
      f"({dataset.row_count} rows, {dataset.column_count} columns{mode})"
    )

  if isinstance(result, DescribeResult):
    dataset = result.dataset
    lines = [
      f"Dataset: {_display_path(dataset.path)}",
      f"Rows: {dataset.row_count}",
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

  if isinstance(result, TransformResult):
    dataset = result.dataset
    return f"{result.message}: {dataset.row_count} rows, {dataset.column_count} columns"

  if isinstance(result, SqlCreateResult):
    dataset = result.dataset
    return f"Created {result.table_name}: {dataset.row_count} rows, {dataset.column_count} columns"

  if isinstance(result, TableResult):
    table_rows = (tuple(_format_cell(value) for value in row) for row in result.rows)
    return "\n".join(_table(result.headers, table_rows))

  if isinstance(result, PlotResult):
    return f"Saved plot: {_display_path(result.path)}"

  raise TypeError(f"Unsupported result: {type(result).__name__}")


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


def _display_path(path: Path) -> str:
  try:
    return str(path.relative_to(Path.cwd()))
  except ValueError:
    return str(path)

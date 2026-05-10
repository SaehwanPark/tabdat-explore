"""Altair-backed artifact rendering for Phase 6 plots."""

from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

import altair as alt

from tabdat.errors import ExecutionError

SUPPORTED_PLOT_EXTENSIONS = {".svg", ".png"}
DEFAULT_PLOT_DIR = Path("artifacts") / "plots"


def default_plot_path(
  command_name: str,
  variables: Sequence[str],
  *,
  artifact_dir: Path = DEFAULT_PLOT_DIR.parent,
  graph_format: str = "svg",
) -> Path:
  slug = "-".join((command_name, *(_slug_part(variable) for variable in variables)))
  return artifact_dir / "plots" / f"{slug}.{graph_format}"


def next_available_plot_path(path: Path) -> Path:
  normalized = path.expanduser()
  if not normalized.exists():
    return normalized

  stem = normalized.stem
  suffix = normalized.suffix
  parent = normalized.parent
  index = 2
  while True:
    candidate = parent / f"{stem}-{index}{suffix}"
    if not candidate.exists():
      return candidate
    index += 1


def save_histogram(
  rows: tuple[tuple[object, ...], ...],
  variable: str,
  path: Path,
  *,
  bins: int | None,
) -> Path:
  chart = (
    _base_chart(rows, (variable,))
    .mark_bar()
    .encode(
      x=alt.X(
        f"{variable}:Q",
        bin=alt.Bin(maxbins=bins) if bins is not None else True,
        title=variable,
      ),
      y=alt.Y("count():Q", title="Count"),
    )
  )
  return _save_chart(chart, path)


def save_scatter(
  rows: tuple[tuple[object, ...], ...],
  y_variable: str,
  x_variable: str,
  path: Path,
) -> Path:
  chart = (
    _base_chart(rows, (y_variable, x_variable))
    .mark_point()
    .encode(
      x=alt.X(f"{x_variable}:Q", title=x_variable),
      y=alt.Y(f"{y_variable}:Q", title=y_variable),
    )
  )
  return _save_chart(chart, path)


def save_bar(
  rows: tuple[tuple[object, ...], ...],
  variable: str,
  path: Path,
) -> Path:
  chart = (
    alt.Chart(alt.Data(values=_rows_to_records(rows, (variable, "count"))))
    .mark_bar()
    .encode(
      x=alt.X(f"{variable}:N", title=variable, sort="-y"),
      y=alt.Y("count:Q", title="Count"),
    )
  )
  return _save_chart(chart, path)


def _base_chart(
  rows: tuple[tuple[object, ...], ...],
  variables: tuple[str, ...],
) -> alt.Chart:
  return alt.Chart(alt.Data(values=_rows_to_records(rows, variables)))


def _rows_to_records(
  rows: tuple[tuple[object, ...], ...],
  columns: tuple[str, ...],
) -> list[dict[str, object]]:
  return [dict(zip(columns, (_json_value(value) for value in row), strict=True)) for row in rows]


def _json_value(value: object) -> object:
  if isinstance(value, Decimal):
    return float(value)
  return value


def _save_chart(chart: alt.Chart, path: Path) -> Path:
  normalized = path.expanduser()
  if normalized.suffix.lower() not in SUPPORTED_PLOT_EXTENSIONS:
    supported = ", ".join(sorted(SUPPORTED_PLOT_EXTENSIONS))
    raise ExecutionError(f"plot saving path must end with one of: {supported}")
  normalized.parent.mkdir(parents=True, exist_ok=True)
  try:
    chart.save(normalized)
  except Exception as exc:
    raise ExecutionError(f"plot could not be saved: {normalized}") from exc
  return normalized


def _slug_part(value: str) -> str:
  normalized = "".join(character if character.isalnum() else "-" for character in value.lower())
  return "-".join(part for part in normalized.split("-") if part) or "plot"

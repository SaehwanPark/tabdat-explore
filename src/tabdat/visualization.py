"""Altair-backed artifact rendering for Phase 6 plots."""

from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import altair as alt
import numpy as np

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
  """Construct a standardized file path for a newly generated plot.

  Generates a sanitized slug name by combining the command name and the variable
  names.

  Args:
    command_name: The name of the plot command (e.g., 'histogram', 'scatter').
    variables: A sequence of column names involved in the plot.
    artifact_dir: Root directory where artifacts are saved.
    graph_format: Format suffix ('svg' or 'png').

  Returns:
    The constructed Path object.
  """
  slug = "-".join((command_name, *(_slug_part(variable) for variable in variables)))
  return artifact_dir / "plots" / f"{slug}.{graph_format}"


def next_available_plot_path(path: Path) -> Path:
  """Find the next available non-conflicting filename for a plot.

  If the path already exists, appends an incrementing index (e.g., '-2', '-3')
  to the filename stem to prevent overwriting existing plots.

  Args:
    path: The base target file path.

  Returns:
    A non-conflicting Path object.
  """
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
  """Generate and save an Altair-based histogram plot.

  Args:
    rows: The raw data rows containing the target variable.
    variable: The name of the variable to bin.
    path: The file path where the plot should be written.
    bins: Optional maximum number of bins.

  Returns:
    The path to the saved plot file.

  Raises:
    ExecutionError: If Altair fails to compile or write the file.
  """
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
  """Generate and save an Altair-based scatter plot.

  Args:
    rows: The raw data rows.
    y_variable: The column name for the Y-axis.
    x_variable: The column name for the X-axis.
    path: The file path where the plot should be written.

  Returns:
    The path to the saved plot file.

  Raises:
    ExecutionError: If Altair fails to compile or write the file.
  """
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
  """Generate and save an Altair-based frequency bar chart for nominal/categorical variables.

  Args:
    rows: Aggregated data rows containing the categorical variable and a 'count' column.
    variable: The categorical column name.
    path: The file path where the plot should be written.

  Returns:
    The path to the saved plot file.

  Raises:
    ExecutionError: If Altair fails to compile or write the file.
  """
  category_order = tuple("<missing>" if row[0] is None else str(row[0]) for row in rows)
  chart_rows = tuple((category, row[1]) for category, row in zip(category_order, rows, strict=True))
  chart = (
    alt.Chart(alt.Data(values=_rows_to_records(chart_rows, (variable, "count"))))
    .mark_bar()
    .encode(
      x=alt.X(f"{variable}:N", title=variable, sort=list(category_order)),
      y=alt.Y("count:Q", title="Count"),
    )
  )
  return _save_chart(chart, path)


def save_bayes_diagnostic_plot(
  idata: object,
  *,
  kind: Literal["trace", "density", "autocorrelation"],
  variables: tuple[str, ...],
  path: Path,
) -> Path:
  """Generate and save Bayesian diagnostic plots using Matplotlib.

  Supports trace plots of MCMC chains, posterior density histograms, and autocorrelation
  lag lines for evaluated variables.

  Args:
    idata: ArviZ InferenceData object containing posterior draws.
    kind: The type of diagnostic plot ('trace', 'density', 'autocorrelation').
    variables: Variable parameter names to plot.
    path: The file path where the plot should be written.

  Returns:
    The path to the saved plot file.

  Raises:
    ExecutionError: If Matplotlib drawing or saving fails.
  """
  import matplotlib.pyplot as plt

  normalized = _validate_plot_path(path)
  normalized.parent.mkdir(parents=True, exist_ok=True)
  figure = None
  try:
    draw_map = _posterior_draws_by_variable(idata, variables)
    figure, axes = plt.subplots(
      len(variables),
      1,
      figsize=(8, max(2.5, 2.2 * len(variables))),
      squeeze=False,
    )
    for axis, variable in zip(axes[:, 0], variables, strict=True):
      chain_draws = draw_map[variable]
      if kind == "trace":
        for chain_index, draws in enumerate(chain_draws):
          axis.plot(draws, linewidth=0.9, label=f"chain {chain_index + 1}")
        axis.legend(loc="best")
        axis.set_ylabel(variable)
      elif kind == "density":
        draws = chain_draws.reshape(-1)
        axis.hist(draws, bins=min(30, max(5, len(draws) // 2)), density=True)
        axis.set_ylabel(variable)
      else:
        for chain_index, draws in enumerate(chain_draws):
          autocorrelation = _autocorrelation_values(draws)
          axis.plot(
            np.arange(len(autocorrelation)), autocorrelation, label=f"chain {chain_index + 1}"
          )
        axis.legend(loc="best")
        axis.set_ylabel(variable)
        axis.set_xlabel("Lag")
    figure.suptitle(f"Bayesian {kind} diagnostics")
    figure.tight_layout()
    figure.savefig(normalized)
  except ExecutionError:
    raise
  except Exception as exc:
    raise ExecutionError(f"plot could not be saved: {normalized}") from exc
  finally:
    if figure is not None:
      plt.close(figure)
  return normalized


def _posterior_draws_by_variable(
  idata: object,
  variables: tuple[str, ...],
) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
  posterior = getattr(idata, "posterior", None)
  if posterior is None:
    raise ExecutionError("plot could not be saved: missing posterior draws")

  draws_by_variable: dict[str, np.ndarray[Any, np.dtype[np.float64]]] = {}
  for variable in variables:
    try:
      values = np.asarray(posterior[variable].values, dtype=float)
    except Exception as exc:
      message = f"plot could not be saved: missing posterior variable {variable}"
      raise ExecutionError(message) from exc
    if values.size == 0:
      raise ExecutionError(f"plot could not be saved: missing posterior variable {variable}")
    if values.ndim < 2:
      raise ExecutionError(f"plot could not be saved: invalid posterior variable {variable}")
    draws_by_variable[variable] = values.reshape(values.shape[0], -1)
  return draws_by_variable


def _autocorrelation_values(
  draws: np.ndarray[Any, np.dtype[np.float64]],
) -> np.ndarray[Any, np.dtype[np.float64]]:
  centered = draws - np.mean(draws)
  denominator = float(np.dot(centered, centered))
  max_lag = min(30, max(1, len(draws) - 1))
  if denominator == 0.0:
    return np.concatenate((np.array([1.0]), np.zeros(max_lag)))
  values = [
    1.0 if lag == 0 else float(np.dot(centered[:-lag], centered[lag:]) / denominator)
    for lag in range(max_lag + 1)
  ]
  return np.asarray(values, dtype=float)


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
  normalized = _validate_plot_path(path)
  normalized.parent.mkdir(parents=True, exist_ok=True)
  try:
    chart.save(normalized)
  except Exception as exc:
    raise ExecutionError(f"plot could not be saved: {normalized}") from exc
  return normalized


def _validate_plot_path(path: Path) -> Path:
  normalized = path.expanduser()
  if normalized.suffix.lower() not in SUPPORTED_PLOT_EXTENSIONS:
    supported = ", ".join(sorted(SUPPORTED_PLOT_EXTENSIONS))
    raise ExecutionError(f"plot saving path must end with one of: {supported}")
  return normalized


def _slug_part(value: str) -> str:
  normalized = "".join(character if character.isalnum() else "-" for character in value.lower())
  return "-".join(part for part in normalized.split("-") if part) or "plot"

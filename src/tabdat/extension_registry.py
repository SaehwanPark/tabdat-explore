"""Internal extension registry contracts for ingestion and estimator adapters.

Declares static configuration mappings defining the data engines and library backends
responsible for processing specific file types and statistical estimators. This registry
supports lazy query pushdown engines (e.g., DuckDB, Polars) and R-based statistical fallbacks
(via rpy2) when Python-native implementations are unavailable.
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

_MODEL_CONFIG = ConfigDict(strict=True, frozen=True)

# Allowed source file tabular formats.
DataFormat = Literal["parquet", "stata", "csv", "feather", "arrow"]

# Allowed Stata-inspired econometric/estimation commands.
EstimatorCommand = Literal[
  "xtabond",
  "tobit",
  "heckman",
  "lasso",
  "postlasso",
  "ridge",
  "elasticnet",
  "cvlasso",
  "cvridge",
  "cvelasticnet",
  "bayes",
  "spregress",
  "dml",
]


@dataclass(config=_MODEL_CONFIG)
class IngestionAdapterSpec:
  """Metadata describing how a specific file format is ingested.

  Attributes:
    data_format: The target format classification (e.g., 'parquet', 'csv').
    adapter_backend: The primary library/framework used for default ingestion.
    supports_lazy: True if the format can be query-optimized or loaded on-demand.
    supported_remote_schemes: Remote URI schemes supported (e.g., 'http', 's3').
    local_lazy_engines: Allowed local engines (e.g., 'duckdb', 'polars') for lazy execution.
    remote_lazy_engines: Allowed remote engines (e.g., 'duckdb') for lazy queries.
  """

  data_format: DataFormat
  adapter_backend: str
  supports_lazy: bool
  supported_remote_schemes: tuple[str, ...]
  local_lazy_engines: tuple[Literal["duckdb", "polars"], ...] = ()
  remote_lazy_engines: tuple[Literal["duckdb", "polars"], ...] = ()


@dataclass(config=_MODEL_CONFIG)
class EstimatorAdapterSpec:
  """Metadata mapping an econometric command to its analytical execution backends.

  Attributes:
    command: The Stata-inspired command identifier (e.g., 'xtabond', 'tobit').
    primary_backend: Canonical Python class or module path to invoke.
    fallback_backend: Optional alternative backend (e.g., R library path via rpy2) if the
      primary Python engine is missing or unsupported.
  """

  command: EstimatorCommand
  primary_backend: str
  fallback_backend: str | None = None


# Static specifications registry defining allowed ingestion behaviors.
_INGESTION_SPECS: tuple[IngestionAdapterSpec, ...] = (
  IngestionAdapterSpec(
    data_format="parquet",
    adapter_backend="duckdb",
    supports_lazy=True,
    supported_remote_schemes=("http", "https", "s3"),
    local_lazy_engines=("duckdb", "polars"),
    remote_lazy_engines=("duckdb",),
  ),
  IngestionAdapterSpec(
    data_format="stata",
    adapter_backend="pandas",
    supports_lazy=False,
    supported_remote_schemes=("http", "https"),
  ),
  IngestionAdapterSpec(
    data_format="csv",
    adapter_backend="duckdb",
    supports_lazy=False,
    supported_remote_schemes=("http", "https"),
  ),
  IngestionAdapterSpec(
    data_format="feather",
    adapter_backend="pyarrow",
    supports_lazy=False,
    supported_remote_schemes=("http", "https"),
  ),
  IngestionAdapterSpec(
    data_format="arrow",
    adapter_backend="pyarrow",
    supports_lazy=False,
    supported_remote_schemes=("http", "https"),
  ),
)

# Static specifications registry mapping estimators to libraries.
_ESTIMATOR_SPECS: tuple[EstimatorAdapterSpec, ...] = (
  EstimatorAdapterSpec(
    command="xtabond",
    primary_backend="python:linearmodels.iv.IVGMM",
    fallback_backend="r:plm::pgmm",
  ),
  EstimatorAdapterSpec(
    command="tobit",
    primary_backend="r:survival::survreg",
    fallback_backend="python:scipy.optimize",
  ),
  EstimatorAdapterSpec(
    command="heckman",
    primary_backend="python:statsmodels.api",
  ),
  EstimatorAdapterSpec(
    command="lasso",
    primary_backend="python:sklearn.linear_model.Lasso",
  ),
  EstimatorAdapterSpec(
    command="postlasso",
    primary_backend="python:sklearn.linear_model.Lasso+statsmodels.OLS",
  ),
  EstimatorAdapterSpec(
    command="ridge",
    primary_backend="python:sklearn.linear_model.Ridge",
  ),
  EstimatorAdapterSpec(
    command="elasticnet",
    primary_backend="python:sklearn.linear_model.ElasticNet",
  ),
  EstimatorAdapterSpec(
    command="cvlasso",
    primary_backend="python:sklearn.linear_model.Lasso",
  ),
  EstimatorAdapterSpec(
    command="cvridge",
    primary_backend="python:sklearn.linear_model.Ridge",
  ),
  EstimatorAdapterSpec(
    command="cvelasticnet",
    primary_backend="python:sklearn.linear_model.ElasticNet",
  ),
  EstimatorAdapterSpec(
    command="bayes",
    primary_backend="python:sklearn.linear_model.BayesianRidge",
  ),
  EstimatorAdapterSpec(
    command="spregress",
    primary_backend="python:spreg",
  ),
  EstimatorAdapterSpec(
    command="dml",
    primary_backend="python:sklearn.linear_model.Lasso+statsmodels.OLS",
  ),
)

_INGESTION_BY_FORMAT = {spec.data_format: spec for spec in _INGESTION_SPECS}
_ESTIMATOR_BY_COMMAND = {spec.command: spec for spec in _ESTIMATOR_SPECS}


def ingestion_adapter_for(data_format: DataFormat) -> IngestionAdapterSpec:
  """Retrieve the ingestion specification for a specific tabular data format.

  Args:
    data_format: The format (e.g., 'csv', 'parquet').

  Returns:
    The IngestionAdapterSpec detailing backend capabilities.
  """
  return _INGESTION_BY_FORMAT[data_format]


def estimator_adapter_for(command: EstimatorCommand) -> EstimatorAdapterSpec:
  """Retrieve the estimator specification for a specific analysis command.

  Args:
    command: The command key (e.g., 'heckman', 'spregress').

  Returns:
    The EstimatorAdapterSpec detailing backend libraries.
  """
  return _ESTIMATOR_BY_COMMAND[command]


def lazy_mode_supported(data_format: DataFormat) -> bool:
  """Check if lazy loading / query pushdown is supported for a format.

  Args:
    data_format: The format class to check.

  Returns:
    True if lazy operations are supported, otherwise False.
  """
  return ingestion_adapter_for(data_format).supports_lazy


def remote_scheme_supported(data_format: DataFormat, scheme: str) -> bool:
  """Verify if a remote URI protocol (e.g., 's3', 'http') is supported for a format.

  Args:
    data_format: The format class to query.
    scheme: The remote URI scheme (e.g. 's3').

  Returns:
    True if the protocol is supported, otherwise False.
  """
  return scheme in ingestion_adapter_for(data_format).supported_remote_schemes


def lazy_engine_supported(
  data_format: DataFormat,
  engine: Literal["duckdb", "polars"],
  *,
  is_remote: bool,
) -> bool:
  """Determine if a query pushdown engine is supported for local/remote access of a format.

  Args:
    data_format: The format class (e.g., 'parquet').
    engine: The engine to evaluate ('duckdb' or 'polars').
    is_remote: True if querying remote storage/URIs, False for local filesystem.

  Returns:
    True if the engine combination is supported, otherwise False.
  """
  spec = ingestion_adapter_for(data_format)
  supported = spec.remote_lazy_engines if is_remote else spec.local_lazy_engines
  return engine in supported

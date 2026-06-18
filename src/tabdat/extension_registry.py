"""Internal extension registry contracts for ingestion and estimator adapters."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

_MODEL_CONFIG = ConfigDict(strict=True, frozen=True)

DataFormat = Literal["parquet", "stata", "csv", "feather", "arrow"]
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
  data_format: DataFormat
  adapter_backend: str
  supports_lazy: bool
  supported_remote_schemes: tuple[str, ...]
  local_lazy_engines: tuple[Literal["duckdb", "polars"], ...] = ()
  remote_lazy_engines: tuple[Literal["duckdb", "polars"], ...] = ()


@dataclass(config=_MODEL_CONFIG)
class EstimatorAdapterSpec:
  command: EstimatorCommand
  primary_backend: str
  fallback_backend: str | None = None


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
    adapter_backend="pandas",
    supports_lazy=False,
    supported_remote_schemes=("http", "https"),
  ),
  IngestionAdapterSpec(
    data_format="arrow",
    adapter_backend="pandas",
    supports_lazy=False,
    supported_remote_schemes=("http", "https"),
  ),
)

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
  return _INGESTION_BY_FORMAT[data_format]


def estimator_adapter_for(command: EstimatorCommand) -> EstimatorAdapterSpec:
  return _ESTIMATOR_BY_COMMAND[command]


def lazy_mode_supported(data_format: DataFormat) -> bool:
  return ingestion_adapter_for(data_format).supports_lazy


def remote_scheme_supported(data_format: DataFormat, scheme: str) -> bool:
  return scheme in ingestion_adapter_for(data_format).supported_remote_schemes


def lazy_engine_supported(
  data_format: DataFormat,
  engine: Literal["duckdb", "polars"],
  *,
  is_remote: bool,
) -> bool:
  spec = ingestion_adapter_for(data_format)
  supported = spec.remote_lazy_engines if is_remote else spec.local_lazy_engines
  return engine in supported

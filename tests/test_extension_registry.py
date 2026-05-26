from tabdat.extension_registry import (
  estimator_adapter_for,
  ingestion_adapter_for,
  lazy_engine_supported,
  lazy_mode_supported,
  remote_scheme_supported,
)


def test_ingestion_registry_contracts() -> None:
  parquet = ingestion_adapter_for("parquet")
  stata = ingestion_adapter_for("stata")

  assert parquet.adapter_backend == "duckdb"
  assert parquet.supported_remote_schemes == ("http", "https", "s3")
  assert parquet.supports_lazy is True
  assert stata.adapter_backend == "pandas"
  assert stata.supported_remote_schemes == ("http", "https")
  assert stata.supports_lazy is False


def test_ingestion_registry_lazy_engine_guards() -> None:
  assert lazy_mode_supported("parquet") is True
  assert lazy_mode_supported("stata") is False
  assert lazy_engine_supported("parquet", "duckdb", is_remote=False) is True
  assert lazy_engine_supported("parquet", "polars", is_remote=False) is True
  assert lazy_engine_supported("parquet", "duckdb", is_remote=True) is True
  assert lazy_engine_supported("parquet", "polars", is_remote=True) is False


def test_ingestion_registry_remote_scheme_guards() -> None:
  assert remote_scheme_supported("parquet", "http") is True
  assert remote_scheme_supported("parquet", "s3") is True
  assert remote_scheme_supported("parquet", "ftp") is False
  assert remote_scheme_supported("stata", "https") is True
  assert remote_scheme_supported("stata", "s3") is False


def test_estimator_registry_contracts() -> None:
  xtabond = estimator_adapter_for("xtabond")
  tobit = estimator_adapter_for("tobit")
  heckman = estimator_adapter_for("heckman")
  lasso = estimator_adapter_for("lasso")

  assert xtabond.primary_backend == "python:linearmodels.iv.IVGMM"
  assert xtabond.fallback_backend == "r:plm::pgmm"
  assert tobit.primary_backend == "r:survival::survreg"
  assert tobit.fallback_backend == "python:scipy.optimize"
  assert heckman.primary_backend == "python:statsmodels.api"
  assert heckman.fallback_backend is None
  assert lasso.primary_backend == "python:sklearn.linear_model.Lasso"
  assert lasso.fallback_backend is None

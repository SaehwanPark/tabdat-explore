"""Differential testing and reference validation against statsmodels / scipy."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import quantreg

from tabdat.executor import Executor
from tabdat.models import (
  LogitRegressionResult,
  PoissonRegressionResult,
  ProbitRegressionResult,
  QregRegressionResult,
  RegressionResult,
  UseCommand,
)
from tabdat.parser import parse_command


def test_reference_validation_matrix_file() -> None:
  matrix_path = Path("docs/reference_validation_matrix.json")
  assert matrix_path.exists()
  with open(matrix_path, encoding="utf-8") as f:
    data = json.load(f)

  assert data["schema_version"] == 1
  tiers = data["tiers"]
  assert "tier_1_foundational" in tiers
  assert "tier_2_econometric" in tiers
  assert "tier_3_advanced" in tiers

  tier1 = tiers["tier_1_foundational"]
  assert len(tier1) >= 8
  for entry in tier1:
    assert entry["validation_status"] == "reference_validated"
    assert "coef_rtol" in entry
    assert "reference_implementation" in entry


def test_diff_regress_classical_ols(tmp_path: Path) -> None:
  rng = np.random.default_rng(42)
  n = 200
  x1 = rng.normal(0, 1, n)
  x2 = rng.normal(2, 1.5, n)
  y = 3.5 + 2.0 * x1 - 1.5 * x2 + rng.normal(0, 0.8, n)

  df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
  data_path = tmp_path / "ols_data.parquet"
  df.to_parquet(data_path)

  # 1. Statsmodels reference fit
  X_sm = sm.add_constant(df[["x1", "x2"]])
  sm_model = sm.OLS(df["y"], X_sm).fit()

  # 2. TabDat execution
  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("regress y x1 x2"))
    assert isinstance(res, RegressionResult)

    # Compare coefficients and standard errors
    tabdat_coefs = {c.name: c for c in res.coefficients}

    # Intercept
    assert np.isclose(tabdat_coefs["intercept"].value, sm_model.params["const"], rtol=1e-5)
    assert tabdat_coefs["intercept"].standard_error is not None
    assert np.isclose(tabdat_coefs["intercept"].standard_error, sm_model.bse["const"], rtol=1e-4)

    # Regressors
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-5)
    assert tabdat_coefs["x1"].standard_error is not None
    assert np.isclose(tabdat_coefs["x1"].standard_error, sm_model.bse["x1"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x2"].value, sm_model.params["x2"], rtol=1e-5)
    assert tabdat_coefs["x2"].standard_error is not None
    assert np.isclose(tabdat_coefs["x2"].standard_error, sm_model.bse["x2"], rtol=1e-4)

    # R2 and Sample size
    assert np.isclose(res.r_squared, sm_model.rsquared, rtol=1e-5)
    assert res.observation_count == sm_model.nobs
  finally:
    executor.close()


def test_diff_regress_robust_hc1(tmp_path: Path) -> None:
  rng = np.random.default_rng(123)
  n = 250
  x1 = rng.uniform(1, 5, n)
  heteroskedastic_noise = rng.normal(0, 0.5 * x1)
  y = 2.0 + 1.8 * x1 + heteroskedastic_noise

  df = pd.DataFrame({"y": y, "x1": x1})
  data_path = tmp_path / "hc1_data.parquet"
  df.to_parquet(data_path)

  # Statsmodels fit with HC1
  X_sm = sm.add_constant(df[["x1"]])
  sm_model = sm.OLS(df["y"], X_sm).fit(cov_type="HC1")

  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("regress y x1, robust"))
    assert isinstance(res, RegressionResult)

    tabdat_coefs = {c.name: c for c in res.coefficients}
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-5)
    assert tabdat_coefs["x1"].standard_error is not None
    assert np.isclose(tabdat_coefs["x1"].standard_error, sm_model.bse["x1"], rtol=1e-4)
    assert tabdat_coefs["intercept"].standard_error is not None
    assert np.isclose(tabdat_coefs["intercept"].standard_error, sm_model.bse["const"], rtol=1e-4)
  finally:
    executor.close()


def test_diff_regress_clustered(tmp_path: Path) -> None:
  rng = np.random.default_rng(999)
  n_clusters = 10
  cluster_size = 25
  n = n_clusters * cluster_size

  cluster_ids = np.repeat(np.arange(n_clusters), cluster_size)
  cluster_effects = rng.normal(0, 1.0, n_clusters)
  x1 = rng.normal(0, 1, n)
  y = 1.0 + 2.5 * x1 + cluster_effects[cluster_ids] + rng.normal(0, 0.5, n)

  df = pd.DataFrame({"y": y, "x1": x1, "cid": cluster_ids})
  data_path = tmp_path / "clustered_data.parquet"
  df.to_parquet(data_path)

  X_sm = sm.add_constant(df[["x1"]])
  sm_model = sm.OLS(df["y"], X_sm).fit(cov_type="cluster", cov_kwds={"groups": df["cid"]})

  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("regress y x1, cluster(cid)"))
    assert isinstance(res, RegressionResult)

    tabdat_coefs = {c.name: c for c in res.coefficients}
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-5)
    assert tabdat_coefs["x1"].standard_error is not None
    assert np.isclose(tabdat_coefs["x1"].standard_error, sm_model.bse["x1"], rtol=1e-4)
  finally:
    executor.close()


def test_diff_logit_mle(tmp_path: Path) -> None:
  rng = np.random.default_rng(77)
  n = 300
  x1 = rng.normal(0, 1, n)
  x2 = rng.normal(0, 1, n)
  z = 0.5 + 1.2 * x1 - 0.8 * x2
  prob = 1 / (1 + np.exp(-z))
  y = (rng.uniform(0, 1, n) < prob).astype(int)

  df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
  data_path = tmp_path / "logit_data.parquet"
  df.to_parquet(data_path)

  X_sm = sm.add_constant(df[["x1", "x2"]])
  sm_model = sm.Logit(df["y"], X_sm).fit(disp=False)

  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("logit y x1 x2"))
    assert isinstance(res, LogitRegressionResult)

    tabdat_coefs = {c.name: c for c in res.coefficients}
    assert np.isclose(tabdat_coefs["intercept"].value, sm_model.params["const"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x2"].value, sm_model.params["x2"], rtol=1e-4)

    assert tabdat_coefs["x1"].standard_error is not None
    assert np.isclose(tabdat_coefs["x1"].standard_error, sm_model.bse["x1"], rtol=1e-3)
    if res.pseudo_r_squared is not None:
      assert np.isclose(res.pseudo_r_squared, sm_model.prsquared, rtol=1e-3)
  finally:
    executor.close()


def test_diff_probit_mle(tmp_path: Path) -> None:
  from scipy.stats import norm

  rng = np.random.default_rng(88)
  n = 300
  x1 = rng.normal(0, 1, n)
  x2 = rng.normal(0, 1, n)
  z = -0.3 + 1.0 * x1 + 0.5 * x2
  prob = norm.cdf(z)
  y = (rng.uniform(0, 1, n) < prob).astype(int)

  df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
  data_path = tmp_path / "probit_data.parquet"
  df.to_parquet(data_path)

  X_sm = sm.add_constant(df[["x1", "x2"]])
  sm_model = sm.Probit(df["y"], X_sm).fit(disp=False)

  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("probit y x1 x2"))
    assert isinstance(res, ProbitRegressionResult)

    tabdat_coefs = {c.name: c for c in res.coefficients}
    assert np.isclose(tabdat_coefs["intercept"].value, sm_model.params["const"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x2"].value, sm_model.params["x2"], rtol=1e-4)
    if res.pseudo_r_squared is not None:
      assert np.isclose(res.pseudo_r_squared, sm_model.prsquared, rtol=1e-3)
  finally:
    executor.close()


def test_diff_poisson_mle(tmp_path: Path) -> None:
  rng = np.random.default_rng(101)
  n = 300
  x1 = rng.normal(0, 0.5, n)
  x2 = rng.normal(0, 0.5, n)
  mu = np.exp(0.5 + 0.8 * x1 - 0.4 * x2)
  y = rng.poisson(mu)

  df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
  data_path = tmp_path / "poisson_data.parquet"
  df.to_parquet(data_path)

  X_sm = sm.add_constant(df[["x1", "x2"]])
  sm_model = sm.Poisson(df["y"], X_sm).fit(disp=False)

  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("poisson y x1 x2"))
    assert isinstance(res, PoissonRegressionResult)

    tabdat_coefs = {c.name: c for c in res.coefficients}
    assert np.isclose(tabdat_coefs["intercept"].value, sm_model.params["const"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x2"].value, sm_model.params["x2"], rtol=1e-4)
  finally:
    executor.close()


def test_diff_qreg(tmp_path: Path) -> None:
  rng = np.random.default_rng(202)
  n = 200
  x1 = rng.uniform(0, 5, n)
  x2 = rng.normal(0, 1, n)
  y = 2.0 + 1.5 * x1 - 0.7 * x2 + rng.laplace(0, 1.0, n)

  df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
  data_path = tmp_path / "qreg_data.parquet"
  df.to_parquet(data_path)

  # Statsmodels median regression (q=0.5)
  sm_model = quantreg("y ~ x1 + x2", df).fit(q=0.5)

  executor = Executor()
  try:
    executor.execute(UseCommand(path=data_path))
    res = executor.execute(parse_command("qreg y x1 x2, quantile(0.5)"))
    assert isinstance(res, QregRegressionResult)

    tabdat_coefs = {c.name: c for c in res.coefficients}
    assert np.isclose(tabdat_coefs["intercept"].value, sm_model.params["Intercept"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x1"].value, sm_model.params["x1"], rtol=1e-4)
    assert np.isclose(tabdat_coefs["x2"].value, sm_model.params["x2"], rtol=1e-4)
  finally:
    executor.close()

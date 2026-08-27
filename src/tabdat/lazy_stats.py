"""Lazy loaders for heavy third-party statistical dependencies."""

from typing import Any


def get_statsmodels_api() -> Any:
  import statsmodels.api as sm

  return sm


def get_statsmodels_conditional_logit() -> Any:
  from statsmodels.discrete.conditional_models import ConditionalLogit

  return ConditionalLogit


def get_statsmodels_count_models() -> tuple[Any, Any]:
  from statsmodels.discrete.count_model import (
    ZeroInflatedNegativeBinomialP,
    ZeroInflatedPoisson,
  )

  return ZeroInflatedPoisson, ZeroInflatedNegativeBinomialP


def get_statsmodels_lowess() -> Any:
  from statsmodels.nonparametric.smoothers_lowess import lowess

  return lowess


def get_statsmodels_linear_reset() -> Any:
  from statsmodels.stats.diagnostic import linear_reset

  return linear_reset


def get_statsmodels_vif() -> Any:
  from statsmodels.stats.outliers_influence import variance_inflation_factor

  return variance_inflation_factor


def get_statsmodels_ols_influence() -> Any:
  from statsmodels.stats.outliers_influence import OLSInfluence

  return OLSInfluence


def get_scipy_stats() -> Any:
  import scipy.stats as stats

  return stats


def get_scipy_optimize() -> Any:
  import scipy.optimize as optimize

  return optimize


def get_linearmodels_iv() -> tuple[Any, Any]:
  from linearmodels.iv import IV2SLS, IVGMM

  return IV2SLS, IVGMM


def get_linearmodels_panel() -> tuple[Any, Any]:
  from linearmodels.panel import PanelOLS, RandomEffects

  return PanelOLS, RandomEffects


def get_sklearn_linear_models() -> tuple[Any, Any, Any, Any]:
  from sklearn.linear_model import (
    BayesianRidge,
    ElasticNet,
    Lasso,
    Ridge,
  )

  return BayesianRidge, ElasticNet, Lasso, Ridge


def get_sklearn_kfold() -> Any:
  from sklearn.model_selection import KFold

  return KFold


def get_spreg_models() -> tuple[Any, ...]:
  from spreg import (
    BaseOLS,
    GM_Combo,
    GM_Combo_Het,
    GM_Error_Het,
    GM_Lag,
    LMtests,
    ML_Error,
    ML_Lag,
    MoranRes,
  )

  return (
    BaseOLS,
    GM_Combo,
    GM_Combo_Het,
    GM_Error_Het,
    GM_Lag,
    LMtests,
    ML_Error,
    ML_Lag,
    MoranRes,
  )


def get_libpysal_knn() -> Any:
  from libpysal.weights import KNN

  return KNN

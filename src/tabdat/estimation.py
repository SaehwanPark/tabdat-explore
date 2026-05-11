"""Phase 12 estimation substrate primitives and shared result contracts.

This module keeps the estimation core pure and typed so later econometric
commands can build thin adapters over stable contracts.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from math import fsum, sqrt
from random import Random
from typing import Protocol, TypeVar

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

_MODEL_CONFIG = ConfigDict(strict=True)

Vector = tuple[float, ...]
Matrix = tuple[tuple[float, ...], ...]

ProblemT = TypeVar("ProblemT", contravariant=True)
ResultT = TypeVar("ResultT", covariant=True)


class Estimator(Protocol[ProblemT, ResultT]):
  def fit(self, problem: ProblemT) -> ResultT: ...


@dataclass(frozen=True, config=_MODEL_CONFIG)
class CoefficientEstimate:
  name: str
  value: float
  standard_error: float | None = None
  statistic: float | None = None
  p_value: float | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class EstimationDiagnostics:
  method: str
  converged: bool
  iterations: int
  objective_value: float | None = None
  residual_sum_of_squares: float | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LeastSquaresProblem:
  predictor_names: tuple[str, ...]
  design_matrix: Matrix
  response: Vector
  include_intercept: bool = True
  intercept_name: str = "intercept"
  weights: Vector | None = None

  def __post_init__(self) -> None:
    _validate_parameter_names(self.predictor_names, "predictor_names")
    _validate_matrix(self.design_matrix, "design_matrix")
    _validate_vector(self.response, "response")
    if len(self.design_matrix) != len(self.response):
      raise ValueError("response length must match design matrix row count")
    if len(self.design_matrix[0]) != len(self.predictor_names):
      raise ValueError("design_matrix column count must match predictor_names length")
    if self.weights is not None:
      _validate_vector(self.weights, "weights")
      if len(self.weights) != len(self.response):
        raise ValueError("weights length must match design matrix row count")
      if any(weight <= 0.0 for weight in self.weights):
        raise ValueError("weights must be positive")
    if self.include_intercept and not self.intercept_name.strip():
      raise ValueError("intercept_name must not be empty")


@dataclass(frozen=True, config=_MODEL_CONFIG)
class LeastSquaresResult:
  parameter_names: tuple[str, ...]
  coefficients: tuple[CoefficientEstimate, ...]
  fitted_values: Vector
  residuals: Vector
  covariance_matrix: Matrix
  diagnostics: EstimationDiagnostics
  observation_count: int
  degrees_of_freedom: int


LogLikelihoodFunction = Callable[[Vector], float]
MomentFunction = Callable[[Vector], Vector]


@dataclass(frozen=True, config=_MODEL_CONFIG)
class MaximumLikelihoodProblem:
  parameter_names: tuple[str, ...]
  initial_parameters: Vector
  log_likelihood: LogLikelihoodFunction

  def __post_init__(self) -> None:
    _validate_parameter_names(self.parameter_names, "parameter_names")
    _validate_parameter_vector(
      parameter_names=self.parameter_names,
      parameters=self.initial_parameters,
      parameter_label="initial_parameters",
    )


@dataclass(frozen=True, config=_MODEL_CONFIG)
class GeneralizedMethodOfMomentsProblem:
  parameter_names: tuple[str, ...]
  moment_names: tuple[str, ...]
  initial_parameters: Vector
  moment_function: MomentFunction
  weight_matrix: Matrix | None = None

  def __post_init__(self) -> None:
    _validate_parameter_names(self.parameter_names, "parameter_names")
    _validate_parameter_names(self.moment_names, "moment_names")
    _validate_parameter_vector(
      parameter_names=self.parameter_names,
      parameters=self.initial_parameters,
      parameter_label="initial_parameters",
    )
    if self.weight_matrix is not None:
      _validate_square_matrix(self.weight_matrix, "weight_matrix")
      if len(self.weight_matrix) != len(self.moment_names):
        raise ValueError("weight_matrix dimension must match moment_names length")


@dataclass(frozen=True, config=_MODEL_CONFIG)
class ParameterEstimateResult:
  parameter_names: tuple[str, ...]
  parameters: Vector
  covariance_matrix: Matrix | None = None
  diagnostics: EstimationDiagnostics | None = None


@dataclass(frozen=True, config=_MODEL_CONFIG)
class BootstrapResult:
  sample_indices: tuple[tuple[int, ...], ...]


def mean(values: Sequence[float | int]) -> float:
  if not values:
    raise ValueError("mean requires at least one value")
  return fsum(float(value) for value in values) / len(values)


def sample_variance(values: Sequence[float | int]) -> float:
  if len(values) < 2:
    raise ValueError("sample variance requires at least two values")
  value_mean = mean(values)
  squared_error_sum = fsum((float(value) - value_mean) ** 2 for value in values)
  return squared_error_sum / (len(values) - 1)


def sample_covariance(
  left: Sequence[float | int],
  right: Sequence[float | int],
) -> float:
  _validate_equal_length(left, right, "sample covariance")
  if len(left) < 2:
    raise ValueError("sample covariance requires at least two paired values")
  left_mean = mean(left)
  right_mean = mean(right)
  covariance_sum = fsum(
    (float(left_value) - left_mean) * (float(right_value) - right_mean)
    for left_value, right_value in zip(left, right, strict=True)
  )
  return covariance_sum / (len(left) - 1)


def covariance_matrix(columns: Sequence[Sequence[float | int]]) -> Matrix:
  if not columns:
    raise ValueError("covariance matrix requires at least one column")
  normalized_columns = tuple(tuple(float(value) for value in column) for column in columns)
  if len(normalized_columns[0]) < 2:
    raise ValueError("covariance matrix requires at least two observations")
  for column in normalized_columns[1:]:
    if len(column) != len(normalized_columns[0]):
      raise ValueError("covariance matrix requires columns of equal length")
  return tuple(
    tuple(sample_covariance(left, right) for right in normalized_columns)
    for left in normalized_columns
  )


def bootstrap_indices(
  sample_size: int,
  replicates: int,
  *,
  seed: int | None = None,
) -> BootstrapResult:
  if sample_size <= 0:
    raise ValueError("sample_size must be positive")
  if replicates < 0:
    raise ValueError("replicates must be non-negative")
  rng = Random(seed)
  sample_indices = tuple(
    tuple(rng.randrange(sample_size) for _ in range(sample_size)) for _ in range(replicates)
  )
  return BootstrapResult(sample_indices=sample_indices)


def fit_least_squares(problem: LeastSquaresProblem) -> LeastSquaresResult:
  design_matrix = _design_matrix_with_optional_intercept(problem)
  response = tuple(float(value) for value in problem.response)
  parameter_names = _least_squares_parameter_names(problem)
  weights = (
    tuple(1.0 for _ in response)
    if problem.weights is None
    else tuple(float(value) for value in problem.weights)
  )
  weighted_design = tuple(
    tuple(sqrt(weight) * entry for entry in row)
    for row, weight in zip(design_matrix, weights, strict=True)
  )
  weighted_response = tuple(
    sqrt(weight) * value for value, weight in zip(response, weights, strict=True)
  )
  xtx = multiply_matrices(transpose_matrix(weighted_design), weighted_design)
  xty = multiply_matrix_vector(transpose_matrix(weighted_design), weighted_response)
  xtx_inverse = invert_matrix(xtx)
  parameters = multiply_matrix_vector(xtx_inverse, xty)
  fitted_values = multiply_matrix_vector(design_matrix, parameters)
  residuals = tuple(
    observed - fitted for observed, fitted in zip(response, fitted_values, strict=True)
  )
  residual_sum_of_squares = fsum(
    weight * residual * residual for weight, residual in zip(weights, residuals, strict=True)
  )
  observation_count = len(response)
  degrees_of_freedom = observation_count - len(parameters)
  sigma_squared = residual_sum_of_squares / degrees_of_freedom if degrees_of_freedom > 0 else 0.0
  covariance = scale_matrix(xtx_inverse, sigma_squared)
  standard_errors = tuple(
    sqrt(max(covariance[index][index], 0.0)) for index in range(len(parameters))
  )
  coefficients = tuple(
    CoefficientEstimate(
      name=name,
      value=value,
      standard_error=standard_error,
      statistic=None if standard_error == 0.0 else value / standard_error,
      p_value=None,
    )
    for name, value, standard_error in zip(
      parameter_names,
      parameters,
      standard_errors,
      strict=True,
    )
  )
  diagnostics = EstimationDiagnostics(
    method="least_squares",
    converged=True,
    iterations=1,
    objective_value=residual_sum_of_squares,
    residual_sum_of_squares=residual_sum_of_squares,
  )
  return LeastSquaresResult(
    parameter_names=parameter_names,
    coefficients=coefficients,
    fitted_values=fitted_values,
    residuals=residuals,
    covariance_matrix=covariance,
    diagnostics=diagnostics,
    observation_count=observation_count,
    degrees_of_freedom=degrees_of_freedom,
  )


def evaluate_log_likelihood(
  problem: MaximumLikelihoodProblem,
  parameters: Vector,
) -> float:
  _validate_parameter_vector(
    parameter_names=problem.parameter_names,
    parameters=parameters,
    parameter_label="parameters",
  )
  return float(problem.log_likelihood(parameters))


def evaluate_moments(
  problem: GeneralizedMethodOfMomentsProblem,
  parameters: Vector,
) -> Vector:
  _validate_parameter_vector(
    parameter_names=problem.parameter_names,
    parameters=parameters,
    parameter_label="parameters",
  )
  moments = tuple(float(value) for value in problem.moment_function(parameters))
  if len(moments) != len(problem.moment_names):
    raise ValueError("moment_function result length must match moment_names length")
  return moments


def predict_linear_response(design_matrix: Matrix, parameters: Vector) -> Vector:
  _validate_matrix(design_matrix, "design_matrix")
  _validate_vector(parameters, "parameters")
  if len(design_matrix[0]) != len(parameters):
    raise ValueError("design_matrix column count must match parameter count")
  return multiply_matrix_vector(design_matrix, parameters)


def mean_and_variance(values: Sequence[float | int]) -> tuple[float, float]:
  return mean(values), sample_variance(values)


def transpose_matrix(matrix: Matrix) -> Matrix:
  _validate_matrix(matrix, "matrix")
  return tuple(tuple(row[index] for row in matrix) for index in range(len(matrix[0])))


def multiply_matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
  _validate_matrix(matrix, "matrix")
  _validate_vector(vector, "vector")
  if len(matrix[0]) != len(vector):
    raise ValueError("matrix column count must match vector length")
  return tuple(
    fsum(entry * value for entry, value in zip(row, vector, strict=True)) for row in matrix
  )


def multiply_matrices(left: Matrix, right: Matrix) -> Matrix:
  _validate_matrix(left, "left")
  _validate_matrix(right, "right")
  if len(left[0]) != len(right):
    raise ValueError("left matrix column count must match right matrix row count")
  right_transposed = transpose_matrix(right)
  return tuple(
    tuple(
      fsum(left_entry * right_entry for left_entry, right_entry in zip(row, column, strict=True))
      for column in right_transposed
    )
    for row in left
  )


def invert_matrix(matrix: Matrix) -> Matrix:
  _validate_square_matrix(matrix, "matrix")
  size = len(matrix)
  augmented = [
    [*map(float, row), *[1.0 if row_index == column_index else 0.0 for column_index in range(size)]]
    for row_index, row in enumerate(matrix)
  ]
  for pivot_index in range(size):
    pivot_row_index = max(
      range(pivot_index, size),
      key=lambda row_index: abs(augmented[row_index][pivot_index]),
    )
    pivot_value = augmented[pivot_row_index][pivot_index]
    if abs(pivot_value) <= 1e-12:
      raise ValueError("matrix is singular and cannot be inverted")
    if pivot_row_index != pivot_index:
      augmented[pivot_index], augmented[pivot_row_index] = (
        augmented[pivot_row_index],
        augmented[pivot_index],
      )
    pivot_value = augmented[pivot_index][pivot_index]
    augmented[pivot_index] = [value / pivot_value for value in augmented[pivot_index]]
    for row_index, row in enumerate(augmented):
      if row_index == pivot_index:
        continue
      factor = row[pivot_index]
      if factor == 0.0:
        continue
      augmented[row_index] = [
        value - factor * pivot_value
        for value, pivot_value in zip(row, augmented[pivot_index], strict=True)
      ]
  return tuple(tuple(row[size:]) for row in augmented)


def scale_matrix(matrix: Matrix, scalar: float) -> Matrix:
  _validate_matrix(matrix, "matrix")
  return tuple(tuple(value * scalar for value in row) for row in matrix)


def _design_matrix_with_optional_intercept(problem: LeastSquaresProblem) -> Matrix:
  if problem.include_intercept:
    return tuple((1.0, *row) for row in problem.design_matrix)
  return problem.design_matrix


def _least_squares_parameter_names(problem: LeastSquaresProblem) -> tuple[str, ...]:
  if problem.include_intercept:
    return (problem.intercept_name, *problem.predictor_names)
  return problem.predictor_names


def _validate_parameter_names(parameter_names: tuple[str, ...], label: str) -> None:
  if not parameter_names:
    raise ValueError(f"{label} must not be empty")
  if any(not name.strip() for name in parameter_names):
    raise ValueError(f"{label} must not contain empty names")


def _validate_parameter_vector(
  *,
  parameter_names: tuple[str, ...],
  parameters: Vector,
  parameter_label: str,
) -> None:
  if len(parameter_names) != len(parameters):
    raise ValueError(f"{parameter_label} length must match parameter_names length")


def _validate_matrix(matrix: Matrix, label: str) -> None:
  if not matrix:
    raise ValueError(f"{label} must not be empty")
  row_length = len(matrix[0])
  if row_length == 0:
    raise ValueError(f"{label} must not contain empty rows")
  for row in matrix[1:]:
    if len(row) != row_length:
      raise ValueError(f"{label} must be rectangular")


def _validate_square_matrix(matrix: Matrix, label: str) -> None:
  _validate_matrix(matrix, label)
  if len(matrix) != len(matrix[0]):
    raise ValueError(f"{label} must be square")


def _validate_vector(vector: Vector, label: str) -> None:
  if not vector:
    raise ValueError(f"{label} must not be empty")


def _validate_equal_length(
  left: Sequence[float | int],
  right: Sequence[float | int],
  label: str,
) -> None:
  if len(left) != len(right):
    raise ValueError(f"{label} inputs must have the same length")


__all__ = [
  "BootstrapResult",
  "CoefficientEstimate",
  "Estimator",
  "EstimationDiagnostics",
  "GeneralizedMethodOfMomentsProblem",
  "LeastSquaresProblem",
  "LeastSquaresResult",
  "MaximumLikelihoodProblem",
  "Matrix",
  "MomentFunction",
  "ParameterEstimateResult",
  "ProblemT",
  "ResultT",
  "Vector",
  "bootstrap_indices",
  "covariance_matrix",
  "evaluate_log_likelihood",
  "evaluate_moments",
  "fit_least_squares",
  "invert_matrix",
  "mean",
  "mean_and_variance",
  "multiply_matrices",
  "multiply_matrix_vector",
  "predict_linear_response",
  "sample_covariance",
  "sample_variance",
  "scale_matrix",
  "transpose_matrix",
]

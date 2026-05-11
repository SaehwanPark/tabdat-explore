import pytest

from tabdat.estimation import (
  GeneralizedMethodOfMomentsProblem,
  LeastSquaresProblem,
  MaximumLikelihoodProblem,
  bootstrap_indices,
  covariance_matrix,
  evaluate_log_likelihood,
  evaluate_moments,
  fit_least_squares,
  mean,
  predict_linear_response,
  sample_covariance,
  sample_variance,
)


def test_scalar_statistical_primitives_and_covariance_matrix() -> None:
  values = (1.0, 2.0, 3.0, 4.0)

  assert mean(values) == pytest.approx(2.5)
  assert sample_variance(values) == pytest.approx(1.6666666666666667)
  assert sample_covariance(values, values) == pytest.approx(1.6666666666666667)

  matrix = covariance_matrix((values, values))

  assert matrix[0][0] == pytest.approx(1.6666666666666667)
  assert matrix[0][1] == pytest.approx(1.6666666666666667)
  assert matrix[1][0] == pytest.approx(1.6666666666666667)
  assert matrix[1][1] == pytest.approx(1.6666666666666667)


@pytest.mark.parametrize(
  ("values", "message", "kind"),
  [
    ((), "mean requires at least one value", "mean"),
    ((1.0,), "sample variance requires at least two values", "variance"),
    ((1.0,), "covariance matrix requires at least two observations", "covariance"),
  ],
)
def test_scalar_statistical_primitives_reject_invalid_inputs(
  values: tuple[float, ...],
  message: str,
  kind: str,
) -> None:
  with pytest.raises(ValueError, match=message):
    if kind == "mean":
      mean(values)
    elif kind == "variance":
      sample_variance(values)
    else:
      covariance_matrix((values, values))


def test_bootstrap_indices_are_deterministic_and_bounded() -> None:
  bootstrap = bootstrap_indices(4, 3, seed=11)

  assert bootstrap.sample_indices == bootstrap_indices(4, 3, seed=11).sample_indices
  assert len(bootstrap.sample_indices) == 3
  assert all(len(sample) == 4 for sample in bootstrap.sample_indices)
  assert all(0 <= index < 4 for sample in bootstrap.sample_indices for index in sample)


def test_fit_least_squares_returns_full_result_contract() -> None:
  problem = LeastSquaresProblem(
    predictor_names=("x",),
    design_matrix=((0.0,), (1.0,), (2.0,)),
    response=(1.0, 3.0, 5.0),
  )

  result = fit_least_squares(problem)

  assert result.parameter_names == ("intercept", "x")
  assert result.coefficients[0].name == "intercept"
  assert result.coefficients[0].value == pytest.approx(1.0)
  assert result.coefficients[1].name == "x"
  assert result.coefficients[1].value == pytest.approx(2.0)
  assert result.fitted_values == pytest.approx((1.0, 3.0, 5.0))
  assert result.residuals == pytest.approx((0.0, 0.0, 0.0))
  assert result.covariance_matrix[0][0] == pytest.approx(0.0)
  assert result.covariance_matrix[1][1] == pytest.approx(0.0)
  assert result.diagnostics.method == "least_squares"
  assert result.diagnostics.converged is True
  assert result.diagnostics.objective_value == pytest.approx(0.0)
  assert result.observation_count == 3
  assert result.degrees_of_freedom == 1


def test_fit_least_squares_rejects_shape_mismatches() -> None:
  with pytest.raises(ValueError, match="response length must match design matrix row count"):
    fit_least_squares(
      LeastSquaresProblem(
        predictor_names=("x",),
        design_matrix=((0.0,), (1.0,)),
        response=(1.0,),
      )
    )

  with pytest.raises(
    ValueError,
    match="design_matrix column count must match predictor_names length",
  ):
    LeastSquaresProblem(
      predictor_names=("x", "y"),
      design_matrix=((0.0,), (1.0,)),
      response=(1.0, 3.0),
    )


def test_estimation_interfaces_validate_contract_shapes() -> None:
  with pytest.raises(
    ValueError,
    match="initial_parameters length must match parameter_names length",
  ):
    MaximumLikelihoodProblem(
      parameter_names=("alpha", "beta"),
      initial_parameters=(0.0,),
      log_likelihood=lambda parameters: -sum(parameters),
    )

  with pytest.raises(ValueError, match="weight_matrix dimension must match moment_names length"):
    GeneralizedMethodOfMomentsProblem(
      parameter_names=("alpha",),
      moment_names=("m1", "m2"),
      initial_parameters=(0.0,),
      moment_function=lambda parameters: (parameters[0],),
      weight_matrix=((1.0,),),
    )


def test_evaluate_contract_functions_validate_shapes() -> None:
  ml_problem = MaximumLikelihoodProblem(
    parameter_names=("alpha", "beta"),
    initial_parameters=(0.0, 0.0),
    log_likelihood=lambda parameters: -sum(parameters),
  )
  gmm_problem = GeneralizedMethodOfMomentsProblem(
    parameter_names=("alpha",),
    moment_names=("moment",),
    initial_parameters=(0.0,),
    moment_function=lambda parameters: (parameters[0],),
  )

  assert evaluate_log_likelihood(ml_problem, (1.5, 2.5)) == pytest.approx(-4.0)
  assert evaluate_moments(gmm_problem, (3.0,)) == pytest.approx((3.0,))

  with pytest.raises(ValueError, match="parameters length must match parameter_names length"):
    evaluate_log_likelihood(ml_problem, (1.0,))

  with pytest.raises(
    ValueError,
    match="moment_function result length must match moment_names length",
  ):
    evaluate_moments(
      GeneralizedMethodOfMomentsProblem(
        parameter_names=("alpha",),
        moment_names=("m1", "m2"),
        initial_parameters=(0.0,),
        moment_function=lambda parameters: (parameters[0],),
      ),
      (1.0,),
    )


def test_predict_linear_response_requires_matching_dimensions() -> None:
  with pytest.raises(ValueError, match="design_matrix column count must match parameter count"):
    predict_linear_response(((1.0, 2.0),), (1.0,))

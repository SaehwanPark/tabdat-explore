# postlasso

## How to invoke

`postlasso linear y x1 x2 [, alpha(<num>) robust noconstant]`

## What it does

Runs Lasso over the candidate predictors, keeps predictors with nonzero selected coefficients,
and refits an ordinary least-squares model on the selected predictors for coefficient inference.

If no predictors are selected, `postlasso` fits an intercept-only model unless `noconstant` is
specified.

## Examples

- `postlasso linear wage educ exper tenure`
- `postlasso linear wage educ exper tenure, alpha(0.05)`
- `postlasso linear wage educ exper tenure, robust`
- `postlasso linear wage educ exper tenure, noconstant`

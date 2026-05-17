# streg

## How to invoke

`streg time_var x1 x2, failure(event_var) dist(weibull|exponential) [robust cluster(var) noconstant]`

## What it does

Fits a bounded parametric survival model with `weibull` or `exponential` likelihood and
deterministic terminal output. `failure(...)` must be a binary event indicator (`0`/`1`), and the
time variable must be strictly positive.

## Options

- `failure(<event_var>)`: required event indicator variable.
- `dist(weibull|exponential)`: required distribution family.
- `robust`: HC-style robust covariance.
- `cluster(<var>)`: clustered covariance.
- `noconstant`: omit intercept.

## Examples

- `streg duration age income, failure(died) dist(weibull)`
- `streg duration age, failure(died) dist(exponential) robust`
- `streg duration age, failure(died) dist(weibull) cluster(firm_id)`

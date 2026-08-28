# `streg`

Fits a bounded parametric survival model with `weibull` or `exponential` likelihood and

deterministic terminal output. `failure(...)` must be a binary event indicator (`0`/`1`), and the

time variable must be strictly positive.

## Syntax

```text
streg time_var x1 x2, failure(event_var) dist(weibull|exponential) [robust cluster(var) noconstant]
```

## Options

- `failure(<event_var>)`: required event indicator variable.
- `dist(weibull|exponential)`: required distribution family.
- `robust`: HC-style robust covariance.
- `cluster(<var>)`: clustered covariance.
- `noconstant`: omit intercept.

## Examples

```text
streg duration age income, failure(died) dist(weibull)
streg duration age, failure(died) dist(exponential) robust
streg duration age, failure(died) dist(weibull) cluster(firm_id)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

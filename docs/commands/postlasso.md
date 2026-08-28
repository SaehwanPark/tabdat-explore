# `postlasso`

Runs Lasso over the candidate predictors, keeps predictors with nonzero selected coefficients,

and refits an ordinary least-squares model on the selected predictors for coefficient inference.

If no predictors are selected, `postlasso` fits an intercept-only model unless `noconstant` is

specified.

## Syntax

```text
postlasso linear y x1 x2 [, alpha(<num>) robust noconstant]
```

## Examples

```text
postlasso linear wage educ exper tenure
postlasso linear wage educ exper tenure, alpha(0.05)
postlasso linear wage educ exper tenure, robust
postlasso linear wage educ exper tenure, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

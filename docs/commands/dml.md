# `dml`

Estimates a partial-linear average treatment effect (ATE) for a binary treatment using

cross-fitted Lasso nuisance models on high-dimensional controls.

## Syntax

```text
dml linear y x1 x2, treat(d) [folds(<int>) alpha(<num>) robust seed(<int>) noconstant]
```

## Examples

```text
dml linear wage educ exper tenure, treat(treated)
dml linear wage educ exper tenure, treat(treated) folds(3)
dml linear wage educ exper tenure, treat(treated) alpha(0.1)
dml linear wage educ exper tenure, treat(treated) robust
dml linear wage educ exper tenure, treat(treated) seed(42)
estat dml
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

# `drdid`

Fit a doubly robust difference-in-differences model to estimate the average treatment effect on the treated (ATT).

!!! question "When to use"
    How do I estimate an average treatment effect on the treated under panel data, adjusting for covariates using outcome regression, propensity score weighting, or both (doubly robust)?

## Syntax

```text
drdid y [covariates], treat(<var>) post(<var>) [method(or|ipw|aipw) robust bootstrap(<n>) seed(<n>)]
```

## Examples

```text
panel firm_id year
drdid wage exper tenure, treat(treated) post(post)
drdid wage exper tenure, treat(treated) post(post) method(ipw)
drdid wage exper, treat(treated) post(post) robust bootstrap(100) seed(42)
estat drdid`  (post-estimation diagnostics: method, cell counts, propensity score summary)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

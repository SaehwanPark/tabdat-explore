# `xtabond`

Fit a bounded dynamic-panel GMM starter model with a lagged dependent term.

!!! question "When to use"
    How do I estimate a simple dynamic-panel relationship with endogeneity-aware lag instrumentation?

## Syntax

```text
xtabond y [xvars] [, robust lags(#) instlag(#)]
```

## Examples

```text
panel firm_id year
xtabond wage exposure
xtabond wage exposure, robust
xtabond wage exposure, lags(2) instlag(3)
estat overid
predict dxb, xb
predict dresid, residuals
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

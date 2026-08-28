# `estat report`

Generate a self-contained interactive HTML dashboard containing regression statistics, parameter estimates, and diagnostic plots (Residuals vs Fitted, Normal Q-Q, Actual vs Fitted) using Altair and Vega-Embed.

## Syntax

```text
estat report [, saving(path) noopen]
```

## Examples

```text
regress wage educ exper` then `estat report
estat report, saving(my_diagnostics.html) noopen
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

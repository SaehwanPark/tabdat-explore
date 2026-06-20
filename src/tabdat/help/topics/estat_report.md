# estat report

How to invoke:
`estat report [, saving(path) noopen]`

What it does:
Generate a self-contained interactive HTML dashboard containing regression statistics, parameter estimates, and diagnostic plots (Residuals vs Fitted, Normal Q-Q, Actual vs Fitted) using Altair and Vega-Embed.

What problem it answers:
What diagnostic visual evidence exists for OLS/WLS regression assumptions, actual vs fitted values, and residual normal distributions?

Examples:
- `regress wage educ exper` then `estat report`
- `estat report, saving(my_diagnostics.html) noopen`

Links:
- `docs/project_proposal.md`
- `docs/dev_phase.md`

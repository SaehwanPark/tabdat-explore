# xtabond

How to invoke:
`xtabond y [xvars] [, robust lags(#) instlag(#)]`

What it does:
Fit a bounded dynamic-panel GMM starter model with a lagged dependent term.

What problem it answers:
How do I estimate a simple dynamic-panel relationship with endogeneity-aware lag instrumentation?

Examples:
- `panel firm_id year`
- `xtabond wage exposure`
- `xtabond wage exposure, robust`
- `xtabond wage exposure, lags(2) instlag(3)`
- `estat overid`
- `predict dxb, xb`
- `predict dresid, residuals`

Links:
- `docs/microecometrics_topics.md`

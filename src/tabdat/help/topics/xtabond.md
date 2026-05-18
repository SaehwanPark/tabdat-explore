# xtabond

How to invoke:
`xtabond y [xvars] [, robust]`

What it does:
Fit a bounded dynamic-panel GMM starter model with a lagged dependent term.

What problem it answers:
How do I estimate a simple dynamic-panel relationship with endogeneity-aware lag instrumentation?

Examples:
- `panel firm_id year`
- `xtabond wage exposure`
- `xtabond wage exposure, robust`

Links:
- `docs/microecometrics_topics.md`

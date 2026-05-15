# cfregress

How to invoke:
`cfregress y exog..., endog(x) iv(z...) [options]`

What it does:
Fit a control-function regression for endogenous predictors.

What problem it answers:
How do I address endogeneity with a residual-inclusion approach?

Examples:
- `cfregress wage educ, endog(experience) iv(distance)`

Links:
- `docs/microecometrics_topics.md`

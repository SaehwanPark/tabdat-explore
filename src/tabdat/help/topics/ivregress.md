# ivregress

How to invoke:
`ivregress 2sls|gmm y exog..., endog(x) iv(z...) [options]`

What it does:
Fit an instrumental-variables regression.

What problem it answers:
How do I estimate a relationship when a predictor is endogenous?

Examples:
- `ivregress 2sls wage educ, endog(experience) iv(distance)`

Links:
- `docs/microecometrics_topics.md`

# lasso

How to invoke:
`lasso linear y x1 x2 [, alpha(<num>) noconstant]`

What it does:
Fit a bounded L1-penalized linear model using a fixed penalty level.

What problem it answers:
How do I shrink coefficients and perform basic linear regularization in one command?

Examples:
- `lasso linear wage educ exper`
- `lasso linear wage educ exper, alpha(0.25)`
- `lasso linear wage educ exper, noconstant`

Links:
- `docs/microecometrics_topics.md`

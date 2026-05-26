# ridge

How to invoke:
`ridge linear y x1 x2 [, alpha(<num>) noconstant]`

What it does:
Fit a bounded L2-penalized linear model using a fixed penalty level.

What problem it answers:
How do I perform ridge regression to handle multicollinearity and shrink coefficients?

Examples:
- `ridge linear wage educ exper`
- `ridge linear wage educ exper, alpha(0.25)`
- `ridge linear wage educ exper, noconstant`

Links:
- `docs/microecometrics_topics.md`

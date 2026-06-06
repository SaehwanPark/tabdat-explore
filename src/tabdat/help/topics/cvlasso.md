# cvlasso

How to invoke:
`cvlasso linear y x1 x2 [, cv(<int>) noconstant]`

What it does:
Perform K-fold cross-validation to select the optimal penalty parameter for an L1-penalized linear model, and save a detailed tuning report.

What problem it answers:
How do I automatically tune the L1 penalty level via cross-validation?

Examples:
- `cvlasso linear wage educ exper`
- `cvlasso linear wage educ exper, cv(10)`
- `cvlasso linear wage educ exper, noconstant`

Links:
- `docs/microecometrics_topics.md`

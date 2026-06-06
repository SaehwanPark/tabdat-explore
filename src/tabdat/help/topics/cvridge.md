# cvridge

How to invoke:
`cvridge linear y x1 x2 [, cv(<int>) noconstant]`

What it does:
Perform K-fold cross-validation to select the optimal penalty parameter for an L2-penalized linear model, and save a detailed tuning report.

What problem it answers:
How do I automatically tune the L2 penalty level via cross-validation?

Examples:
- `cvridge linear wage educ exper`
- `cvridge linear wage educ exper, cv(10)`
- `cvridge linear wage educ exper, noconstant`

Links:
- `docs/microecometrics_topics.md`

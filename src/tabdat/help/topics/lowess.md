# lowess

How to invoke:
`lowess y x, gen(<newvar>) [bandwidth=<0,1>]`

What it does:
Generate a nonparametric LOWESS-smoothed fit column.

What problem it answers:
How do I inspect a smooth nonlinear relationship without imposing a parametric form?

Examples:
- `lowess wage exper, gen(wage_lowess)`
- `lowess wage exper, gen(wage_lowess) bandwidth=0.5`

Links:
- `docs/microecometrics_topics.md`

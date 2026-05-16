# zinb

How to invoke:
`zinb y x1 x2, inflate(z1 z2) [robust cluster(var) noconstant]`

What it does:
Fit a zero-inflated negative-binomial count-response model with a logit inflation equation.

What problem it answers:
How do I model overdispersed count outcomes with excess zeros and a separate zero process?

Examples:
- `zinb visits age income, inflate(age income)`
- `zinb claims age exposure, inflate(exposure) cluster(firm_id)`

Links:
- `docs/microecometrics_topics.md`

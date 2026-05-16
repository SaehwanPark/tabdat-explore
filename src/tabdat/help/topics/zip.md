# zip

How to invoke:
`zip y x1 x2, inflate(z1 z2) [robust cluster(var) noconstant]`

What it does:
Fit a zero-inflated Poisson count-response model with a logit inflation equation.

What problem it answers:
How do I model count outcomes with excess zeros and a separate zero-generation process?

Examples:
- `zip visits age income, inflate(age income)`
- `zip claims age exposure, inflate(exposure) robust`

Links:
- `docs/microecometrics_topics.md`

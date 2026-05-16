# nbreg

How to invoke:
`nbreg y x1 x2 [, robust cluster(var) noconstant]`

What it does:
Fit a negative-binomial count-response model.

What problem it answers:
How do I model overdispersed non-negative count outcomes as a function of predictors?

Examples:
- `nbreg visits age income`
- `nbreg claims age exposure, robust`

Links:
- `docs/microecometrics_topics.md`

# elasticnet

How to invoke:
`elasticnet linear y x1 x2 [, alpha(<num>) l1_ratio(<num>) noconstant]`

What it does:
Fit a bounded L1- and L2-penalized linear model using a fixed penalty level.

What problem it answers:
How do I combine L1 and L2 penalties to perform elastic net regularization?

Examples:
- `elasticnet linear wage educ exper`
- `elasticnet linear wage educ exper, alpha(0.25) l1_ratio(0.75)`
- `elasticnet linear wage educ exper, noconstant`

Links:
- `docs/microecometrics_topics.md`

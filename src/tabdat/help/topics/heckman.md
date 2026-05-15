# heckman

How to invoke:
`heckman y x1 x2, selectdep(z) select(z1 z2) [options]`

What it does:
Fit a sample-selection model with an outcome equation and a selection equation.

What problem it answers:
How do I correct for non-random selection into the observed sample?

Examples:
- `heckman wage educ exper, selectdep(work) select(age kids)`

Links:
- `docs/microecometrics_topics.md`

# did

How to invoke:
`did y [controls], treat(<var>) post(<var>) [robust]`

What it does:
Fit a bounded two-way fixed-effects difference-in-differences model.

What problem it answers:
How do I estimate an average treatment effect using panel data with treated and post indicators?

Examples:
- `panel firm_id year`
- `did wage exposure, treat(treated) post(post)`
- `did wage exposure, treat(treated) post(post) robust`

Links:
- `docs/microecometrics_topics.md`

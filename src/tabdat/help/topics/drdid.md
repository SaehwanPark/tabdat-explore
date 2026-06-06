# drdid

How to invoke:
`drdid y [covariates], treat(<var>) post(<var>) [method(or|ipw|aipw) robust bootstrap(<n>) seed(<n>)]`

What it does:
Fit a doubly robust difference-in-differences model to estimate the average treatment effect on the treated (ATT).

What problem it answers:
How do I estimate an average treatment effect on the treated under panel data, adjusting for covariates using outcome regression, propensity score weighting, or both (doubly robust)?

Examples:
- `panel firm_id year`
- `drdid wage exper tenure, treat(treated) post(post)`
- `drdid wage exper tenure, treat(treated) post(post) method(ipw)`
- `drdid wage exper, treat(treated) post(post) robust bootstrap(100) seed(42)`

Links:
- `docs/microecometrics_topics.md`

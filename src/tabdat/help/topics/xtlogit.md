# xtlogit

How to invoke:
`xtlogit y xvars, fe [robust]`

What it does:
Fit a bounded fixed-effects panel logit model for a binary outcome.

What problem it answers:
How do I estimate within-entity binary-choice effects with panel data?

Examples:
- `panel firm_id year`
- `xtlogit promoted training tenure, fe`
- `xtlogit promoted training tenure, fe robust`

Links:
- `docs/microecometrics_topics.md`

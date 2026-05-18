# estat

How to invoke:
`estat <subcommand>`

What it does:
Run postestimation diagnostics and model-specific summaries.

What problem it answers:
How do I check fit, identification, or marginal effects after estimation?

Examples:
- `estat vif`
- `estat residuals`
- `qreg claims age exposure` then `estat residuals`
- `estat margins`
- `estat gof`
- `nbreg claims age exposure` then `estat gof`
- `zinb claims age exposure, inflate(exposure)` then `estat gof`
- `did claims age exposure, treat(treated) post(post)` then `estat did`

Links:
- `docs/microecometrics_topics.md`

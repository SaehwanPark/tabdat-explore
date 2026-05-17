# qreg

How to invoke:
`qreg y x1 x2 [, quantile(<0,1>) robust noconstant]`

What it does:
Fit a bounded quantile regression model for a selected conditional quantile.

What problem it answers:
How do I model conditional medians or other conditional quantiles instead of mean effects?

Examples:
- `qreg cost age bmi`
- `qreg cost age bmi, quantile(0.25)`
- `qreg cost age bmi, robust`

Links:
- `docs/microecometrics_topics.md`

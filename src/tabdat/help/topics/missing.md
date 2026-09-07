# missing

How to invoke:
`missing [varlist]`

What it does:
Show total, missing, nonmissing, and missing-percentage counts for active dataset columns. Missing
means an explicit null under TabDat's existing missingness policy; empty strings and user-defined
sentinel codes are not treated as missing.

What problem it answers:
Which columns have missing data, and how much?

Examples:
- `missing`
- `missing age income`

The report preserves schema or requested variable order. It computes a bounded aggregate scan for
Polars-lazy datasets without switching them to eager mode. Use `codebook` when you also need types,
distinct counts, and example values.

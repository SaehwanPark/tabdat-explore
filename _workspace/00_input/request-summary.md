# Request Summary: Tabulate Value-Label Display (Loop 2)

## Goal
When variables have attached value labels, `tabulate` displays those labels in category cells and wide column headers by default (Stata/SPSS-style), with `nolabel` to show raw codes.

## Constraints
- Inspired, not compatible; no estimator expansion.
- Ordering and missingness rules unchanged (still sort/group on raw values).
- One branch / one PR.

## Non-goals
- Changing bar chart labels; encode/decode; persisting labels.

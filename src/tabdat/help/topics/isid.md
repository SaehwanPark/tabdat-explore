# isid

Assert that one or more key variables uniquely identify active rows.

## Syntax

```text
isid varlist [, missok]
```

Without `missok`, any null key component fails the check. With `missok`, null-containing keys are
allowed only when their complete key combination is unique. Repeated null combinations still fail.

```text
tabdat> isid patient_id visit
isid passed
Key variables: patient_id visit
Rows checked: 3
Unique groups: 3
Rows with missing keys: 0
Missing keys allowed: no
```

`isid` is read-only and supports eager, DuckDB-lazy, and Polars-lazy execution. It accepts no row
filter, assignment, `by:` prefix, or options other than the `missok` flag.

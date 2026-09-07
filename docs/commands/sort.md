# `sort`

Stable-sort the active dataset by ascending native scalar keys.

## Syntax

```text
sort <varlist>
```

Sort keys are applied left to right. Nulls sort last and ties preserve the prior active-row order.
The command keeps all columns and preserves variable/value labels and panel metadata.

```text
tabdat> sort treatment age
Sorted by: treatment age
Rows: 100, Columns: 6
```

`sort` preserves Polars-lazy mode by updating its lazy plan. Descending keys, expression keys, and
deduplication are intentionally out of scope; use SQL when you need those operations.

## See also

- [`head`](head.md)
- [`tail`](tail.md)
- [Language Semantics](../language-semantics.md)
- [Command Reference Index](../command-reference/index.md)

# `missing`

Report explicit-null missingness for the active dataset.

## Syntax

```text
missing [varlist]
```

With no variables, all columns are reported in schema order. A variable list is reported in the
order requested. The report includes total rows, missing rows, nonmissing rows, and missing percent.
Empty strings and user-defined sentinel codes are not treated as missing.

```text
tabdat> missing age income
Variable | Type    | Total | Missing | Nonmissing | Missing %
---------+---------+-------+---------+------------+----------
age      | INTEGER | 100   | 4       | 96         | 4
income   | DOUBLE  | 100   | 12      | 88         | 12
```

`missing` is read-only. On a Polars-lazy dataset it performs the aggregate scan without switching
the session to eager mode. Use [`codebook`](codebook.md) for distinct counts and example values.

## See also

- [`codebook`](codebook.md)
- [Language Semantics](../language-semantics.md)
- [Command Reference Index](../command-reference/index.md)

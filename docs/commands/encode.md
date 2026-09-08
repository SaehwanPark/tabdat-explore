# `encode`

Convert a string variable into a new integer-coded variable (1..K for sorted unique nonmissing values), create a matching value-label set, and attach it.

!!! question "When to use"
    Turn string categories into numeric codes with value labels for tabulate and modeling.

## Syntax

```text
encode <strvar>, generate(<newvar>) [, label(<lblname>)]
```

## Options

- `generate(<newvar>)`: Required. Name of the new integer variable to create.
- `label(<lblname>)`: Optional. Name of the value-label set to create (defaults to `<newvar>`).

## Examples

```text
encode sex, generate(sex_n)
encode region, generate(region_id) label(regionlbl)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

# `decode`

Convert a numeric variable that has attached value labels into a new string variable of those labels. Codes without labels become missing.

!!! question "When to use"
    Recover readable string categories from a labeled numeric variable.

## Syntax

```text
decode <numvar>, generate(<newvar>)
```

## Options

- `generate(<newvar>)`: Required. Name of the new string variable to create.

## Examples

```text
decode sex_n, generate(sex_str)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

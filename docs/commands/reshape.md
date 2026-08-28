# `reshape`

Convert between wide and long layouts.

!!! question "When to use"
    How do I pivot repeated-measures data into the shape I need?
    
    Long output follows source-row order. Its j-values scan requested stubs in command order, then matching
    
    wide columns in schema order, keeping each suffix's first appearance once.
    
    Wide output follows the first active row for each identifier group; existing generated-column and
    
    duplicate-cell behavior remains unchanged.

## Syntax

```text
reshape long|wide varlist, i(idvars) j(jvar)
```

## Examples

```text
reshape long income cost, i(id) j(year)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

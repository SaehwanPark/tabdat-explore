# `bar`

Save a bar chart for a categorical variable.

!!! question "When to use"
    How are category counts distributed?
    
    Nonmissing bars are ordered by descending count; ties use the category's native order and the missing category is always last when `missing` is requested. Numeric labels use numeric order rather than rendered text, and missing displays as `<missing>`.
    
    If a literal category label is `<missing>`, it is disambiguated from the missing category in the chart.

## Syntax

```text
bar varname [, missing saving(path) noopen]
```

## Examples

```text
bar sex
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

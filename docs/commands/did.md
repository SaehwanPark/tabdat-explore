# `did`

Fit a bounded two-way fixed-effects difference-in-differences model.

!!! question "When to use"
    How do I estimate an average treatment effect using panel data with treated and post indicators?

## Syntax

```text
did y [controls], treat(<var>) post(<var>) [robust]
```

## Examples

```text
panel firm_id year
did wage exposure, treat(treated) post(post)
did wage exposure, treat(treated) post(post) robust
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

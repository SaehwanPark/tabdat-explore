# `doctor`

Inspect and report the operational health and capability status of the TabDat environment, including core engines, statistics backends, optional extensions (ML, Bayesian, Spatial, R), and system runtime metadata.

!!! question "When to use"
    Which TabDat backends and capabilities are available, and what are their installed versions?

## Syntax

```text
doctor
```

## Examples

```text
doctor
tabdat doctor
tabdat --json doctor
Notes:
doctor` is a pure diagnostic and introspection command; it does not mutate dataset state.
In terminal mode, it outputs an aligned capability matrix with checkmarks and library versions.
In JSON mode, it outputs structured data containing `core`, `statistics`, `optional`, and `system` arrays.
Optional capabilities that are not installed are reported with actionable missing package hints.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

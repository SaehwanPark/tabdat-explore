# doctor

How to invoke:
`doctor`

What it does:
Inspect and report the operational health and capability status of the TabDat environment, including core engines, statistics backends, optional extensions (ML, Bayesian, Spatial, R), and system runtime metadata.

What problem it answers:
Which TabDat backends and capabilities are available, and what are their installed versions?

Examples:
- `doctor`
- `tabdat doctor`
- `tabdat --json doctor`

Notes:
- `doctor` is a pure diagnostic and introspection command; it does not mutate dataset state.
- In terminal mode, it outputs an aligned capability matrix with checkmarks and library versions.
- In JSON mode, it outputs structured data containing `core`, `statistics`, `optional`, and `system` arrays.
- Optional capabilities that are not installed are reported with actionable missing package hints.

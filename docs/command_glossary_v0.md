# Command Glossary v0

This glossary defines the first small command surface for TabDat-Explore. It is intentionally high level. Detailed syntax, output, and error behavior should be written in a command contract before implementation.

## Inspection And Loading

### `use`

Load a dataset into the single active dataset slot.

Phase 1 focus: load Parquet from a local path.

### `describe`

Show dataset structure, including columns, types, and basic shape.

Phase 1 focus: describe the active dataset.

### `summarize`

Show descriptive statistics for one or more variables.

Phase 1 focus: summarize numeric columns for the active dataset.

### `codebook`

Show compact column-level profiling, including type, missingness, and representative values.

Phase 3 focus.

### `count`

Count rows in the active dataset, optionally after a filter in a later phase.

Phase 3 focus.

### `head`

Preview the first rows of the active dataset.

Phase 3 focus.

### `tail`

Preview the last rows of the active dataset where the backend can support it predictably.

Phase 3 focus.

## Transformation

### `keep`

Keep selected variables or, in a later phase, rows matching a condition.

Phase 3 focus.

### `drop`

Drop selected variables or, in a later phase, rows matching a condition.

Phase 3 focus.

### `rename`

Rename one variable while preserving data and type.

Phase 3 focus.

### `generate`

Create a new variable from an expression.

Phase 3 focus after expression parsing exists.

## Summaries

### `tabulate`

Produce one-way or two-way frequency tables.

Phase 3 focus.

## Deferred Commands

The following commands are important but should remain outside the v0 command set until the core workflow is stable:

- `replace`
- `select`
- `collapse`
- `by:`
- `sql`
- `histogram`
- `scatter`
- `bar`
- `run`
- `set`

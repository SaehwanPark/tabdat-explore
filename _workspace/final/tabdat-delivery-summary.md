# Phase 11 Reshape Delivery Summary

## Summary

Implemented the third Phase 11 data workflow primitive on branch
`codex/tmp-phase11-reshape-wide-long`.

## Changed Behavior

- `reshape long <stublist>, i(<id_vars>) j(<name_var>)` reshapes active wide data into long rows.
- `reshape wide <value_vars>, i(<id_vars>) j(<name_var>)` pivots active long data into wide columns.
- Reshape results replace the active dataset and are materialized eagerly.
- Successful commands print `Reshaped long: N rows, M columns` or
  `Reshaped wide: N rows, M columns`.

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Known Limits

- Only active-dataset reshape is supported.
- Long reshape requires `<stub>_<j_value>` source columns.
- Wide reshape emits `<value_var>_<j_value>` columns.
- No custom separators, aliases, panel metadata, script variables/macros, seeding, control flow,
  remote access, or Phase 12 estimation substrate work was added.

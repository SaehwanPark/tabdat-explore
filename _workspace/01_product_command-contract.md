# Command Contract: tabulate value-label display

## Syntax addition
`tabulate ... [, nolabel]`

`nolabel` is a flag. Existing options unchanged.

## Semantics
- If a tabulate dimension variable has an attached value-label set, mapped category values render as their label text in:
  - one-way category cells
  - wide table row-index cells
  - wide table column-header category fragments
- Unmapped values (including missing) keep existing rendering (`str(value)` / `missing`).
- Sorting, grouping, percents, and counts use raw values (labels are display-only).
- `nolabel` disables all value-label substitution for that command.
- `by:` tabulate inherits the same rules.

## Acceptance
- Parser accepts/rejects `nolabel` correctly.
- Executor/backend tests: labeled one-way and two-way; `nolabel` restores codes; unmapped stays raw.
- Help topic mentions labels + `nolabel`.
- Focused pytest + ruff + basedpyright + docs alignment.

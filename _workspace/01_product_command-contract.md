# Phase 14 Slice 4 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 4: panel-indexing transforms (`xtdata`)

## `xtdata`

### Syntax

```stata
xtdata <varlist>, within
xtdata <varlist>, between
```

### Rules

- Requires an active dataset.
- Requires prior panel metadata from `panel <id_var> <time_var>`.
- Requires at least one variable.
- Requires exactly one transform option: `within` or `between`.
- Variables must be numeric.
- Adds transformed columns and preserves existing rows:
  - `within`: append `<var>_within = var - entity_mean(var)`
  - `between`: append `<var>_between = entity_mean(var)`
- If a target column already exists, fail deterministically.

### User-facing errors

- Missing panel metadata:
  - `xtdata requires panel metadata; run panel <id_var> <time_var> first`
- Invalid command shape:
  - `xtdata expects syntax: xtdata <varlist>, within|between`
- Invalid transform selection:
  - `xtdata requires exactly one of within or between`
- Non-numeric variables:
  - `xtdata requires numeric variables: <vars>`
- Target collision:
  - `xtdata target already exists: <vars>`
- Execution failure:
  - `xtdata failed`

## Acceptance Criteria

- Parser accepts valid forms and rejects malformed forms deterministically.
- Executor appends deterministic transformed columns with preserved row count and panel metadata.
- CLI/shell tests cover command success and completion paths.
- Full quality checks pass (`ruff`, `pyright`, `mypy`, `pytest`).
- SDD/docs and `_workspace` artifacts reflect delivered behavior.

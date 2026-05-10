# Phase 9-10 Future Items Command Contract

## Request Summary

Finish the remaining documented Phase 9 and Phase 10 future items by adding extension-driven
multi-format export and a bounded real Polars lazy execution slice.

## Roadmap Phase

- Phase 9: Configuration & Environment
- Phase 10: Execution & State Foundations

## Export Contract

### Syntax

```stata
save filtered.parquet
export filtered.parquet, replace
export filtered.csv
export filtered.feather, replace
```

Rules:

- `save` remains local Parquet only.
- `export` chooses the output format from the path suffix.
- Supported export suffixes are `.parquet`, `.csv`, and `.feather`.
- `replace` keeps its current meaning for both `save` and `export`.
- Parent directories are created automatically when needed.
- Session state is not mutated by `save` or `export`.

### User-Facing Errors

- Unsupported export suffix: `export only supports .parquet, .csv, and .feather files`
- Existing target without replace: `export target already exists: <path>`
- Non-file existing target: `export target is not a file: <path>`
- Writer failure: `export failed: <path>`

### User-Facing Output

- `save` keeps `Saved: <path> (<rows> rows, <columns> columns)`.
- `export` reports `Exported: <path> (<rows> rows, <columns> columns)`.

## Polars Lazy Contract

### Syntax

```stata
use data.parquet, lazy engine=polars
```

Rules:

- `use <local parquet path>, lazy engine=polars` creates a real Polars lazy active dataset.
- The active dataset remains lazy for:
  - `describe`
  - `count`
  - `head`
  - `tail`
  - `select`
  - `keep <varlist>`
  - `drop <varlist>`
  - `keep if <expr>`
  - `drop if <expr>`
- Unsupported commands may materialize the active dataset once into the existing eager DuckDB
  path before continuing.
- After fallback materialization, the active dataset reports eager execution mode, a known row
  count, and `lazy_engine=None`.
- Existing eager DuckDB behavior remains unchanged.
- Remote Parquet handling is not expanded in this slice.

### User-Facing Errors

- If Polars cannot create the lazy scan: `use could not read Parquet file: <path>`
- If a Polars-only unsupported path needs a broader redesign, stop the implementation and report
  the mismatch instead of changing command semantics.

## Acceptance Criteria

- Parser tests cover `export` paths with `.parquet`, `.csv`, and `.feather`.
- Executor tests cover export success and error paths for all supported suffixes.
- CLI tests cover `Exported:` output and artifact creation.
- Executor tests prove that bounded Polars lazy commands preserve lazy state.
- Executor tests prove that at least one unsupported command materializes once and then runs
  successfully through the eager path.
- `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and `_workspace/` artifacts all describe the same
  supported export formats, the same bounded Polars subset, and the same remaining limits.

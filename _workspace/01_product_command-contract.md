# Command Contract: `label`

## Request summary
Session-local variable labels and named value-label sets, surfaced in `describe`/`codebook`.

## Roadmap phase
Forward roadmap: deepen terminal EDA (data-dictionary UX). Not an estimator expansion. Exception to “breadth freeze” is recorded as bounded metadata for existing EDA commands.

## Command syntax

```text
label variable <varname> "text"
label variable <varname>, clear

label define <lblname> <value> "text" [<value> "text" ...] [, replace]
label values <varname> <lblname>
label values <varname>, clear

label list
label list <lblname> [<lblname> ...]
label drop <lblname> [<lblname> ...]
```

### Rules
- Command name is case-insensitive; label-set names and variable names are case-sensitive exact spellings.
- Variable-label text and value-label text must be quoted strings.
- Value keys may be numeric literals or quoted/unquoted string literals; stored exactly as parsed (ints preferred when whole numbers).
- `label define` fails if the set exists unless `replace` is set (full replace of mappings).
- `label values` requires an existing set and an existing variable.
- `label drop` removes sets; attachments referencing dropped sets are cleared.
- Failed label mutations leave dataset metadata unchanged (atomicity).

## Examples

| Input | Expected |
|-------|----------|
| `label variable age "Age in years"` | Sets variable label; confirms in message |
| `label define sexlbl 0 "Male" 1 "Female"` | Creates set `sexlbl` |
| `label values sex sexlbl` | Attaches set to `sex` |
| `label list` | Lists variable labels, sets, and attachments |
| `describe` | Shows a Label column with variable labels (`.` if none) |
| `codebook sex` | Shows variable label when present |
| `label variable missing_col "x"` | Error: unknown variable |
| `label define sexlbl 0 "M"` when exists | Error unless `, replace` |

## Non-goals
Labeled `tabulate` display, persistence to Parquet, `encode`/`decode`, SPSS `.sav` I/O.

## Data assumptions
Requires an active dataset for all `label` forms. Metadata lives on `DatasetInfo.label_metadata`. Column drops/keeps prune variable labels and attachments for missing columns; value sets remain until `label drop`. Rename retargets variable labels and attachments.

## Execution semantics
Pure session metadata updates (no backend query except column existence checks via schema). No materialization.

## Acceptance criteria
- Focused parser tests for all valid/invalid forms above.
- Executor tests for set/list/drop, describe/codebook surfacing, rename/drop preservation, atomic failure.
- CLI smoke: `-c` sequence set labels then `describe`.
- Help topic `label`, command-reference row, effects=`control`, schema entry.
- `uv run pytest` (focused then full as needed), ruff, basedpyright, docs alignment.

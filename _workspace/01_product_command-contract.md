# Command Contract: label save / label use

## Product and roadmap fit

Phase 24A data-dictionary stabilization. This is a TabDat-native, Stata/SAS/SPSS-inspired metadata workflow, not a claim of native `.dta`, SAS catalog, or `.sav` compatibility.

## Syntax

```text
label save <path> [, replace]
label use <path>
```

`<path>` is a UTF-8 JSON dictionary file. Paths may be quoted when they contain spaces. `replace` is valid only for `label save`.

## Semantics

- Both commands require an active dataset because the dictionary describes the active dataset's variables.
- `label save` writes a deterministic UTF-8 JSON document with `schema_version: 1` and the current variable labels, value-label sets, and variable attachments. It does not change the active dataset or force a lazy scan.
- `label use` reads and validates one `schema_version: 1` dictionary, then attaches it to the active dataset atomically. Existing metadata is replaced only after the file, schema, mappings, and variable references validate.
- Dictionaries may contain an empty metadata set; loading one clears the current metadata.
- Variable-label and attachment references must name columns in the active dataset. Every attachment must reference a value-label set in the same dictionary. Mapping values are JSON numbers or strings and labels are strings; duplicate set names, attachment names, or mapping values are rejected.
- `label save` refuses an existing path unless `replace` is supplied. Parent directories are not created implicitly.
- Malformed JSON, unsupported schema versions, invalid metadata, missing files, unknown variables, and unknown value-label references produce an execution error and leave active data, labels, execution mode, and last-operation metadata unchanged.
- `label use` on a Polars-lazy dataset validates against the lazy schema and does not materialize the dataset. `label save` also does not materialize it.

## JSON shape

```json
{
  "metadata": {
    "attachments": [["sex", "sexlbl"]],
    "value_sets": [
      {"mappings": [[0, "Male"], [1, "Female"]], "name": "sexlbl"}
    ],
    "variable_labels": [["age", "Age in years"]]
  },
  "schema_version": 1
}
```

Keys and metadata sequences are emitted deterministically. The schema version is reserved for future incompatible dictionary formats.

## Examples

```text
label variable age "Age in years"
label define sexlbl 0 "Male" 1 "Female"
label values sex sexlbl
label save labels.json, replace

use another.parquet, lazy engine=polars
label use labels.json
```

Expected save output: `Saved label dictionary: labels.json`.
Expected use output: `Loaded label dictionary: labels.json`.

## Invalid forms

- `label save` / `label use` without a path: parse error.
- `label save labels.json, clear` or `label use labels.json, replace`: parse error.
- `label use missing.json`: execution error; current metadata remains unchanged.
- A dictionary referring to `missing_var` or an unknown label set: execution error; no partial attachment.
- `label save labels.json` when the target exists: execution error unless `, replace` is present.

## Acceptance

- Parser tests cover both forms, quoting, `replace`, and option errors.
- Pure serialization tests cover deterministic versioned JSON and malformed/schema/type rejection.
- Executor tests cover round-trip metadata, atomic incompatible loads, overwrite behavior, and Polars-lazy no-materialization behavior.
- CLI tests cover human output and JSON result envelopes.
- Help, command reference, command schema, and declared effects are aligned (`label` gains read/write/control effects).
- Validate with focused tests, full `pytest`, docs alignment, ruff, formatting, and basedpyright.

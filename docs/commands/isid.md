# `isid`

`isid` is a read-only key-uniqueness quality gate inspired by Stata's `isid`, SAS key-validation
workflows, and SPSS duplicate-ID validation. It makes a composite-key invariant explicit and
scriptable without changing the active dataset.

## Syntax

```text
isid varlist [, missok]
```

`missok` is the only supported option. At least one key variable is required.

## Semantics

- Each complete key combination must occur at most once.
- Null key values compare equal for duplicate grouping, so repeated null-containing combinations fail.
- Without `missok`, any row with a null in any key variable fails even when that incomplete key is
  otherwise unique.
- With `missok`, incomplete keys are allowed only when their complete combinations remain unique.
- Empty datasets pass with zero rows and zero unique groups.
- Unknown variables are rejected before scanning. The command is read-only and preserves labels,
  panel metadata, named tables, and the active lazy plan.
- Eager, DuckDB-lazy, and Polars-lazy execution use aggregate scans.

## Output

```text
isid passed
Key variables: patient_id visit
Rows checked: 3
Unique groups: 3
Rows with missing keys: 0
Missing keys allowed: no
```

JSON output uses `result_type: "IsidResult"` with `variables`, `total_rows`, `unique_groups`,
`missing_key_rows`, and `missok` fields.

Failures use deterministic command-level errors, for example:

```text
isid failed: 2 rows have missing key values (use , missok to permit them); 3 rows are in 1 duplicate key groups
```

## Examples

```text
use visits.parquet, lazy engine=polars
isid patient_id visit
isid patient_id visit, missok
```

The first form requires every key component to be present; the second allows incomplete keys only when
those combinations are unique.

## Invalid forms

```text
isid
isid patient_id if active == true
isid patient_id, report
isid patient_id, missok(true)
isid missing_column
```

These forms fail with deterministic parse or execution errors and do not mutate active state.

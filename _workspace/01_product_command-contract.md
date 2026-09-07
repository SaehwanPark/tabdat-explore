# Command Contract: `assert`

## Product and roadmap fit

`assert` is a read-only active-row quality gate inspired by Stata `assert`, SAS data checks, and
SPSS validation workflows. It is TabDat-native and intentionally does not promise native compatibility.
It extends terminal EDA/data-quality work without expanding estimator families.

## Syntax

```text
assert <boolean-expression>
```

The expression uses TabDat's existing identifiers, literals, comparison/arithmetic operators,
parentheses, and supported functions. The command accepts no options, `if` clause, assignment, or
by-prefix.

## Semantics

- Requires an active dataset and one syntactically valid boolean expression.
- A row passes when the predicate evaluates to true. False or missing/null predicate results count as
  failures. This makes missing checks explicit rather than silently passing unknown values.
- The command checks every active row. An empty active dataset passes with `checked = 0` and
  `failed = 0`.
- A successful command returns `AssertResult(checked, failed=0)` and records the usual command history
  operation; it does not replace or mutate the active relation, schema, labels, panel metadata, or
  named-table contents.
- A failed command raises `ExecutionError` with deterministic checked and failed counts. The active
  relation and session data state remain unchanged; the command does not emit a successful result.
- DuckDB eager/lazy and Polars-lazy execution use aggregate scans. Polars-lazy remains lazy and is not
  replaced by an eager frame.
- Existing expression type, identifier, arithmetic, null, and function semantics are reused. A
  predicate must infer to boolean or null; unknown variables and unsupported expressions fail before
  the aggregate query.

## Output

Human success output:

```text
assertion passed: 3 rows
```

The structured result is:

```json
{
  "schema_version": 1,
  "result_type": "AssertResult",
  "data": {"checked": 3, "failed": 0}
}
```

Failure uses the existing error envelope/type with a deterministic message such as:

```text
assertion failed: 1 of 3 rows failed
```

## Examples

```text
use survey.parquet, lazy engine=polars
assert age >= 0
assert bmi != null
```

The second example intentionally fails for rows whose BMI is null; use `bmi == null` when checking
for missing values explicitly.

## Invalid forms

- `assert`: parse error; a predicate is required.
- `assert age`: execution error; predicates must be boolean or null.
- `assert age > 0, strict`: parse error; options are unsupported.
- `assert age > 0 if sex == "F"`: parse error; `if` clauses are unsupported.
- `assert age = 0`: parse error; assignment syntax is unsupported.
- `assert missing > 0`: execution error; unknown variables are rejected.

## Acceptance

- Parser tests cover comparison/function/quoted-identifier expressions, required predicates, and
  rejected options, `if`, and assignment forms.
- Backend/executor tests cover true/false/missing rows, empty datasets, non-boolean predicates,
  unknown variables, deterministic failure counts, unchanged state, and eager/DuckDB-lazy/
  Polars-lazy execution.
- CLI tests cover human success/failure, JSON success/error envelopes, and no-active-dataset errors.
- Help, command reference/navigation, language semantics, command schema/effects, and shell completion
  are aligned.
- Validate with focused tests, full `pytest`, docs alignment, Ruff, formatting, basedpyright, and
  hosted CI.

---

# Command Contract: `duplicates`

## Product and roadmap fit

`duplicates` is a read-only duplicate-key quality report inspired by Stata `duplicates report`,
SAS `PROC SORT`/`NODUPKEY` workflows, and SPSS duplicate-case inspection. It complements TabDat's
`missing` and `assert` checks while preserving the single-active-dataset and modern aggregate-scan
architecture. It is TabDat-native rather than a promise of syntax compatibility with those tools.

## Syntax

```text
duplicates [report] [varlist]
```

- `report` is an optional, case-insensitive unquoted subcommand alias.
- With no varlist, all public columns in schema order form the duplicate key.
- A varlist preserves the spelling and order supplied by the user; backtick-quoted identifiers are
  supported by the existing command grammar.
- The command accepts no options, `if` clause, assignment, `list`, `drop`, or `tag` operation.

## Semantics

- Requires an active dataset and validates every requested key before scanning rows.
- A duplicate group is a set of rows with equal key values. SQL null values are equal to one another
  for this report, so rows missing the same key values are grouped together intentionally.
- The report counts every row in a duplicate group (`duplicate_rows`) and also reports the surplus
  rows after retaining one representative (`extra_rows`). It never changes the active relation.
- `total_rows` is the number of active rows; `unique_groups` is the number of distinct key
  combinations; `duplicate_groups` counts groups with at least two rows; `max_copies` is the largest
  group size, or zero for an empty dataset.
- An empty dataset returns all zero counts. Unknown variables and malformed syntax fail before any
  state change.
- DuckDB eager/lazy and Polars-lazy execution use aggregate grouping. A Polars-lazy report collects
  only aggregate output and leaves the active plan lazy, with no eager fallback or row listing.
- The command is read-only and records normal command history; active rows, schema, labels, panel
  metadata, named tables, and materialization metadata remain unchanged.

## Output

Human output:

```text
Duplicates report
Key variables: id name
Rows: 5
Unique groups: 3
Duplicate groups: 1
Rows in duplicate groups: 3
Extra duplicate rows: 2
Maximum copies: 3
```

The structured result is:

```json
{
  "schema_version": 1,
  "result_type": "DuplicatesResult",
  "data": {
    "variables": ["id", "name"],
    "total_rows": 5,
    "unique_groups": 3,
    "duplicate_groups": 1,
    "duplicate_rows": 3,
    "extra_rows": 2,
    "max_copies": 3
  }
}
```

## Examples

```text
use survey.parquet, lazy engine=polars
duplicates report id
# Equivalent shorthand:
duplicates id name
```

## Invalid forms

- `duplicates, missing`: parse error; options are unsupported.
- `duplicates id if age > 0`: parse error; filtering is outside the read-only report.
- `duplicates id = other`: parse error; assignment is unsupported.
- `duplicates missing_column`: execution error; unknown key variables are rejected.

## Acceptance

- Parser tests cover shorthand/default/report-alias forms, quoted identifiers, required rejection of
  options/conditions/assignment, and exact malformed syntax.
- Backend/executor tests cover all-column and requested-key reports, null grouping, no duplicates,
  duplicate groups/surplus counts, empty datasets, unknown variables, unchanged state, and eager,
  DuckDB-lazy, and Polars-lazy execution.
- CLI tests cover deterministic human output, JSON success envelope, no-active-dataset errors, and
  read-only command-effect/schema/help/completion integration.
- Help, command reference/navigation, language semantics, command schema/effects, shell completion,
  `SPEC.md`, architecture, and changelog remain aligned.
- Validate with focused tests, full `pytest`, docs alignment, Ruff, formatting, basedpyright, and
  the repository verification profile.

---

# Command Contract: `datasignature`

## Product and roadmap fit

`datasignature` is a read-only reproducibility and data-integrity fingerprint inspired by Stata 19
`datasignature`, SAS `PROC COMPARE`, and SPSS validation workflows. It gives terminal analysts a
small, machine-readable way to record whether the active data values and schema changed, without
adding a proprietary metadata store, mutating the dataset, or claiming compatibility with those
products. It is a bounded Phase 24 stabilization improvement: a deterministic trust primitive rather
than a new estimator or broad comparison framework.

## Syntax

```text
datasignature
```

The command accepts no varlist, options, `if` clause, assignment, or `by:` prefix.

## Semantics

- Requires an active dataset and scans all public columns in schema order.
- The SHA-256 signature covers a versioned TabDat framing header, canonicalized public column names
  and logical types, active row order, and every cell value. Nulls, booleans, strings, numbers,
  temporal values, decimals, bytes, and nested list/tuple/dict values use explicit deterministic
  encodings; non-finite floats receive explicit tokens.
- Schema and row order are intentionally included because TabDat treats the active relation's ordered
  sequence as meaningful. Session-local variable/value labels, panel metadata, source path, backend,
  and execution mode are not part of the signature.
- The signature is a full read-only scan. Eager and DuckDB-lazy use bounded Python row batches;
  Polars-lazy uses `collect_batches` and leaves the original lazy plan active. No active relation,
  labels, panel metadata, named tables, or materialization state is changed.
- The result also reports the scanned row and public-column counts. Empty datasets are valid and
  return a schema-dependent signature with zero rows.
- This is a TabDat-native fingerprint, not a byte-for-byte Parquet checksum: equivalent data stored
  in supported execution modes should produce the same signature, while changing a value, schema,
  null, or row order should change it.

## Output

Human success output:

```text
Data signature
Algorithm: sha256
Rows: 3
Columns: 4
Signature: <64 lowercase hexadecimal characters>
```

The structured result is:

```json
{
  "schema_version": 1,
  "result_type": "DatasignatureResult",
  "data": {
    "algorithm": "sha256",
    "signature": "<64 lowercase hexadecimal characters>",
    "row_count": 3,
    "column_count": 4
  }
}
```

## Examples

```text
use survey.parquet, lazy engine=polars
datasignature
```

A script can record the JSON `signature` and compare it before rerunning a reproducible analysis.

## Invalid forms

- `datasignature age`: parse error; the command fingerprints the complete active dataset.
- `datasignature, fast`: parse error; algorithm shortcuts and machine-dependent modes are outside the
  initial contract.
- `datasignature if age > 0`: parse error; filtered signatures are not defined.
- `datasignature = value`: parse error; the command is read-only.
- `datasignature` without an active dataset: execution error with the standard no-active-dataset
  behavior.

## Acceptance

- Parser tests cover the exact no-argument form and reject varlists, options, conditions, and
  assignment syntax.
- Backend/executor tests cover deterministic signatures, null/non-finite/temporal values, schema and
  row-order sensitivity, empty datasets, unchanged state, equivalent eager/DuckDB-lazy/Polars-lazy
  signatures, and unknown/no-active failure behavior.
- CLI tests cover human output, JSON envelope, no-active-dataset errors, command schema/effects/help,
  and shell completion.
- Help, command reference/navigation, user-guide reproducibility guidance, architecture/spec/changelog,
  and MCP EDA guidance remain aligned.
- Validate with focused tests, full `pytest`, docs alignment, Ruff, formatting, basedpyright, wheel
  packaging, and hosted CI.

---

# Command Contract: `gsort`

## Product and roadmap fit

`gsort` extends TabDat's stable ascending `sort` with explicit per-key directions, inspired by Stata's
`gsort`, SAS `PROC SORT` descending keys, and SPSS `SORT CASES` order directives. It is a bounded
Phase 24 ordering slice: it adds useful ordering expressiveness while keeping native scalar ordering,
nulls-last placement, stable ties, eager/lazy parity, and the single-active-dataset model.

## Syntax

```text
gsort [+|-]varlist
```

- Each key may begin with `+` for ascending or `-` for descending; an omitted prefix means ascending.
- Keys are applied left-to-right. Ties preserve their previous active-row order.
- A backtick-quoted identifier is never interpreted as a direction prefix, so a quoted variable named
  `` `-score` `` can be addressed literally.
- The command accepts no options, `if` clause, assignment, or `by:` prefix.

## Semantics

- Requires at least one key and validates all variables before changing the active relation.
- Numeric, text, boolean, date, timestamp, decimal, and other supported scalar keys use the existing
  native comparison semantics. Missing/null keys are always placed after nonmissing values, even for
  descending keys.
- The sort is stable: rows tied on every requested key retain their prior order. An internal ordinal
  tie-breaker is used only to make this guarantee explicit and is not retained in the public schema.
- Eager/DuckDB-lazy and Polars-lazy execution use the backend's native stable sort. Polars-lazy stays
  lazy; failure leaves the prior plan and session metadata unchanged.
- The command mutates active row order and records the normal transform result. Schema, labels, panel
  metadata, and named-table synchronization follow existing `sort` behavior.

## Output

Human output uses the existing transform result:

```text
Sorted by: -group_id +label
```

JSON output uses the existing `TransformResult` envelope with the same message and updated dataset.

## Examples

```text
gsort -date +patient_id
gsort +site -score
```

## Invalid forms

- `gsort`: parse error; at least one key is required.
- `gsort group_id, stable`: parse error; options are unsupported.
- `gsort group_id if active == true`: parse error; filtering is outside this ordering command.
- `gsort -`: parse error; a direction prefix must be followed by a variable name.
- `gsort --score`: parse error; use one optional direction prefix per key.
- `gsort missing_column`: execution error; unknown variables are rejected before mutation.

## Acceptance

- Parser tests cover omitted/explicit ascending and descending keys, mixed directions, quoted
  identifiers, and malformed/rejected forms.
- Backend/executor tests cover stable mixed-direction ordering, nulls-last for ascending and
  descending keys, unknown-variable atomicity, metadata preservation, and eager/DuckDB-lazy/
  Polars-lazy behavior.
- CLI tests cover human/JSON transform output, schema/effects/help, and no-active-dataset errors;
  shell tests cover command and column completion.
- Help, command reference/navigation, language semantics, README, architecture/spec/changelog, MCP
  guidance, and roadmap records remain aligned.
- Validate with focused tests, full `pytest`, docs alignment, Ruff, formatting, basedpyright, wheel
  packaging, and hosted CI.

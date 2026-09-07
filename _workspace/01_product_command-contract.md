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

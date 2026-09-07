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

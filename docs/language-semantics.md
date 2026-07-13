# TabDat Language Semantics

This document records stable cross-command behavior. It covers identifier spelling, quoting, explicit
missing values, expression domains, arithmetic results, write-target, and failure semantics;
ordering, randomness, estimation samples, and exit behavior remain separate contracts.

## Identifier spelling and quoting

- Bare identifiers preserve their exact spelling and are case-sensitive. `age` and `Age` refer to
  different variables; command names remain case-insensitive.
- A bare identifier starts with a Unicode letter or `_`, followed by Unicode letters, digits, or `_`.
- Backtick-quoted identifiers can contain whitespace and punctuation. They are accepted for variable
  targets, variable lists, and expression references, and their contents are preserved exactly.
- Inside a backtick-quoted identifier, two consecutive backticks represent one literal backtick.
  Empty quoted identifiers are invalid.
- SQL text keeps SQL's own identifier rules; this command-language contract does not rewrite SQL.

For example:

```text
generate `age group` = age + 1
replace `weight kg` = `weight kg` * 2 if `status flag` == "active"
```

Quoted identifiers are not command names or option names. An exact spelling mismatch remains an
unknown-variable error and follows the write-validation atomicity policy below.

## Explicit missing values and predicates

- The unquoted token `null` is a case-insensitive missing-value literal. A quoted `` `null` `` is
  still an ordinary identifier with exact spelling.
- `value == null` and `null == value` are true only for missing values; `value != null` and
  `null != value` are true only for nonmissing values.
- `null == null` is true and `null != null` is false.
- A direct `null` expression can generate or replace an all-missing value and can be used as a row
  predicate. It follows the existing keep/drop policy below.
- Null used with another comparison operator, unary arithmetic, or a function is rejected with a
  stable execution error. This slice does not add `is null`, `missing()`, or `nonmissing()` syntax.

## Missing values and predicates

- Missing values are represented as null values (`None` at the Python boundary); this slice does not
  introduce a special numeric missing sentinel.
- `keep if expression` retains only rows where the expression is true. False and missing predicate
  results are not kept.
- `drop if expression` removes only rows where the expression is true. False and missing predicate
  results remain in the active dataset.
- `replace name = expression if condition` updates only true-condition rows. False and missing
  conditions preserve the existing value.
- `summarize` counts nonmissing numeric values; its means, minima, and maxima ignore missing values.
  `codebook` reports nonmissing and missing counts explicitly.
- `tabulate` and `bar` omit missing categories by default. Their `missing` option includes missing
  categories where the command supports it; bar charts display that category as `<missing>`.

## Expression domains and coercion

- Numeric columns and numeric literals share one `numeric` domain. Numeric widening within that
  domain is allowed; values are not parsed from or stringified into text implicitly.
- Unsafe combinations of unsigned numeric columns and negative numeric literals are rejected
  consistently rather than relying on backend-specific signed/unsigned coercion.
- Text values and string literals share the `string` domain. Boolean values and comparison results
  use the `boolean` domain. Other backend scalar types are not coerced into either domain.
- Equality/inequality and ordering require matching domains, except for numeric pairs and the
  existing null-aware equality/inequality rules.
- Arithmetic and unary minus require numeric operands. String concatenation is not defined here.
- Numeric functions (`abs`, `ceil`, `floor`, `ln`, `log`, `round`, `sqrt`) require numeric arguments;
  `lower` and `upper` require string arguments.
- `keep`, `drop`, `replace if`, and `tabulate if` require boolean or missing conditions. Numeric or
  string truthiness is rejected.
- `replace` permits null or an expression in the target's domain; cross-domain assignment is
  rejected before the active relation changes.
- Mixed-domain failures use deterministic type-mismatch diagnostics, and Polars-lazy validation
  occurs before fallback materialization.

## Arithmetic results and non-finite values

- Arithmetic operators `+`, `-`, `*`, and `/`, plus unary minus, continue to require numeric
  operands. A valid finite result remains in the numeric domain; exact backend-specific storage
  widening is not promised.
- Missing operands propagate to missing results. The explicit `null` literal remains rejected by
  arithmetic and functions; this rule covers missing values supplied by data columns.
- Division is real division. A zero denominator, including `0 / 0`, produces a missing result for
  that row rather than infinity or NaN.
- `sqrt(x)` produces missing when `x < 0`; `ln(x)` and `log(x)` produce missing when `x <= 0`.
- Any computed NaN or infinity from supported arithmetic or numeric functions is normalized to
  missing. A direct identifier does not rewrite a non-finite value already present in the source.
- Subtraction involving an unsigned numeric column and unary minus of an unsigned numeric expression
  are rejected before execution; wraparound and implicit signed widening are not inferred.
- The policy is row-level: valid rows remain usable in `generate`, `replace`, and arithmetic
  predicates while affected rows become missing and follow the existing predicate rules.

## Grouped-result ordering

- `by summarize`, `by count`, `collapse`, and long-form `tabulate` sort grouping dimensions in
  native scalar order with missing values last. Numeric values sort numerically; strings sort
  lexicographically; booleans sort false before true.
- Wide-form `tabulate` uses the same native order for row keys and column headers. Numeric labels are
  not ordered by their rendered text, so `2` precedes `10`.
- `bar` sorts nonmissing categories by descending count, then native category order for ties; the
  missing category is always last.
- SQL without explicit `order by` and categorical ordering remain separate contracts.

## Active row order

- The active dataset has one current row sequence; source order is the initial sequence.
- `head n` returns the first `n` rows and `tail n` returns the last `n` rows in sequence order,
  restoring the tail rows to their original relative order. A zero limit returns no rows.
- `keep if` and `drop if` preserve the relative order of retained rows. False and missing predicate
  results follow the existing keep/drop policy and never reorder survivors.
- Column projection and row-preserving value transformations preserve the current row sequence.
- Grouped or relation-changing commands such as `collapse`, append, join, and reshape establish
  separate result-sequence contracts; this slice does not redefine their later preview order.
- Categorical order remains a separate contract.

## SQL and named-table row order

- A direct SQL result follows the row sequence produced by its query. An explicit `order by` defines
  the listed-key order; a reproducible total sequence requires tie-breaker keys that distinguish
  tied rows. SQL without `order by` has no guarantee here.
- `sql ... into name` stores and activates the query result without reordering it. `use name` restores
  that stored sequence, and `head`/`tail` consume it using the active row-order rules.
- SQL remains an eager boundary for named-table creation; a Polars-lazy input uses the existing
  fallback path before the query executes, and successful named-table activation resets the prior
  materialization reason.
- Append/join/reshape order and categorical order remain separate contracts.

## Write targets

| Command family | Target rule | Failure behavior |
|---|---|---|
| `generate name = expression` | `name` must not already exist | Reject the collision; do not replace the active relation |
| `rename old new` | `old` must exist and `new` must not exist | Reject either invalid source/destination before replacement |
| `replace name = expression` | `name` must already exist | Reject the missing target; do not create it implicitly |
| `recode ..., generate(names)` | one output per input; outputs must be unique and new | Validate all outputs before changing the active relation |

The diagnostics identify the target/source problem. Existing wording is covered by focused tests
and can only change through a later language-error contract.

## Atomic validation failures

Write commands validate target existence, source existence, output cardinality, and expression
requirements before replacing the active relation. A validation failure preserves:

- active columns and their order;
- active rows and values;
- execution mode, lazy engine, and active table metadata;
- last-successful-operation and materialization-reason metadata.

This is an active-dataset boundary guarantee. It does not promise rollback of unrelated external
side effects, such as an already-created artifact file from another command.

## Deliberate limits

Categorical behavior, exact arithmetic storage widths, overflow diagnostics, append/join/reshape
ordering, SQL without explicit ordering, randomness, estimation samples, machine-readable output,
and exit codes are not defined here yet.

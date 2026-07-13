# TabDat Language Semantics

This document records stable cross-command behavior. It covers identifier spelling, quoting, explicit
missing values, expression domains, write-target, and failure semantics; ordering, randomness,
estimation samples, and exit behavior remain separate contracts.

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

Coercion, arithmetic, categorical behavior, ordering, randomness, estimation samples, machine-readable
output, and exit codes are not defined here yet.

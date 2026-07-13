# TabDat Language Semantics

This document records stable cross-command behavior. It starts with identifier spelling, quoting,
write-target, and failure semantics; missing values, coercion, ordering, randomness, estimation
samples, and exit behavior remain separate contracts.

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

Missing values, coercion, arithmetic, categorical behavior, ordering, randomness, estimation samples,
machine-readable output, and exit codes are not defined here yet.

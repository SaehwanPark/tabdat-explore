# TabDat Language Semantics

This document records stable cross-command behavior. It starts with write-target and failure
semantics; identifier quoting, missing values, coercion, ordering, randomness, estimation samples,
and exit behavior remain separate contracts.

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

Identifier case/quoting, missing values, coercion, arithmetic, categorical behavior, ordering,
randomness, estimation samples, machine-readable output, and exit codes are not defined here yet.

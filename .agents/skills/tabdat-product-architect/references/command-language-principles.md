# TabDat Command Language Principles

## Product Position

TabDat is Stata-inspired, not Stata-compatible. Borrow the concise command ergonomics, but prefer modern data behavior, explicit errors, and predictable scripting over legacy quirks.

## Early Grammar Target

Start small:

```text
command [varlist] [, options]
```

Add `if` conditions, expression parsing, and `by:` only after the core command path is reliable.

## Contract Checklist

For each command, define:

- canonical syntax
- one minimal example
- one realistic example
- required active dataset state
- behavior for missing columns
- behavior for unsupported types
- output columns and formatting expectations
- backend operation or planned abstraction
- tests and smoke command

## Scope Guardrails

- Prefer 10 solid commands over many partial commands.
- Do not add autocomplete, plotting, lazy optimization, or R integration as hidden prerequisites for early parser work.
- Treat SQL as an escape hatch, not the primary command language.
- Keep visualization output artifact-based when plotting arrives.

## Error Style

Errors should name the command, the invalid input, and the smallest useful correction. Avoid backend-native errors leaking directly to users when a command-level message is possible.

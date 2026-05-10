# TabDat QA Checklist

## Cross-Boundary Checks

Command contract to docs:

- roadmap phase matches the implemented scope
- examples in the contract do not contradict project docs
- non-goals were not implemented accidentally

Contract to parser:

- valid syntax parses to the expected structured representation
- invalid syntax returns command-level errors
- options and varlists are not silently ignored

Parser to executor:

- executor consumes the parser representation directly
- semantic validation happens outside raw parsing
- missing active dataset and missing columns are handled consistently

Executor to backend:

- backend receives explicit operations, table names, and columns
- result shape is structured and deterministic
- backend-native exceptions are converted where appropriate

Backend to formatter and CLI:

- displayed output matches the contract examples
- numeric summaries are stable enough for tests
- empty, missing, and unsupported data cases have readable messages

Tests to claimed behavior:

- tests cover the success path and at least one error path
- smoke tests exercise user-visible command behavior
- validation commands in the implementation report match the tests that actually ran

## Report Template

```markdown
# QA Report

Status: pass | fix | redo

## Boundaries Checked
- ...

## Blocking Issues
- ...

## Non-Blocking Follow-Ups
- ...

## Validation Evidence
- command: `...`
- outcome: ...

## Recommended Next Action
...
```

# Request Summary: encode / decode (Loop 3)

## Goal
Add Stata/SPSS-inspired `encode` and `decode` for string↔numeric conversion with automatic value-label creation/use.

## Syntax
```
encode <strvar>, generate(<newvar>) [label(<lblname>)]
decode <numvar>, generate(<newvar>)
```

## Semantics
- `encode`: string source → new integer codes 1..K for sorted unique nonmissing values; creates/replaces label set (default name = newvar) and attaches it; missing stays missing.
- `decode`: numeric source with attached value labels → new string column of labels; unmapped nonmissing codes become missing; missing stays missing.
- Fail if source missing, wrong type, generate target exists, or decode has no attached labels.
- Preserve panel/label metadata appropriately (new columns get attachments for encode).

## Non-goals
- In-place encode without generate; SPSS AUTOMATIC RECODE extras; label language.

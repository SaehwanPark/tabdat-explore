# Phase 11 Script Primitives Command Contract

## Request Summary

Add the next unfinished Phase 11 reproducibility primitive slice: script-local seeds and reusable
macros.

## Roadmap Phase

Phase 11: Data Workflow & Reproducibility Primitives.

## Script Syntax

```stata
seed <integer>
let <name> = <value>
```

Rules:

- `seed <integer>` records a deterministic integer seed for the current script run.
- `let <name> = <value>` records a reusable script macro.
- `$name` expands to a previously defined macro value in later script entries.
- Macro names must be identifiers matching `[A-Za-z_][A-Za-z0-9_]*`.
- Macro values are the trimmed text after `=`.
- Macro values may reference previously defined macros.
- `seed` may reference macros after expansion.
- `seed` and `let` are script-only directives, not interactive or executor commands.

## Examples

```stata
seed 123
let data = patients.parquet
use $data
let adults = age >= 18
keep if $adults
```

## Execution Semantics

- Script directive state is scoped to one top-level script run.
- Nested `run <script>` calls share the parent script's macro and seed state.
- A macro may only be defined once in a top-level script run.
- Macro expansion happens immediately before a script entry is echoed and executed.
- Expansion applies to regular commands and directive bodies.
- Missing macro references fail before command parsing or execution.
- `seed` updates script metadata only; no random operations are introduced in this slice.
- `-c "run <script>"`, `tabdat -f <script>`, positional script execution, and interactive `run`
  use the same directive semantics.

## User-Facing Output

- `seed 123` echoes as `. seed 123` and prints `Seed: 123`.
- `let data = patients.parquet` echoes as `. let data = patients.parquet` and prints
  `Macro set: data`.
- Regular commands echo after macro expansion, for example `. use patients.parquet`.
- Script metadata prints `Seed: none` before any seed is set and the current seed for nested
  scripts after a seed is set.

## User-Facing Errors

- Invalid seed: `seed expects an integer`
- Invalid macro syntax: `let expects syntax: let <name> = <value>`
- Invalid macro name: `macro name must be an identifier: <name>`
- Empty macro value: `macro value cannot be empty: <name>`
- Duplicate macro: `macro already defined: <name>`
- Undefined macro: `undefined macro: <name>`

## Non-Goals

- No inline comments.
- No macro overwrite or unset command.
- No quoting or escaping rules beyond plain text replacement.
- No control flow, loops, or conditionals.
- No remote data access.
- No random sampling, simulation, or estimation command behavior.

## Acceptance Criteria

- Script tests cover directive parsing, macro expansion, nested sharing, and diagnostics.
- CLI tests cover deterministic top-level script output, nested script state sharing, and
  line-numbered macro failures.
- Existing command-mode, shell, parser, executor, and script behavior remains compatible.
- Documentation records the Phase 11 script directive boundary and remaining future Phase 11 work.

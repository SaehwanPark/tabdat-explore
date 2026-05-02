# Phase 2 Command Contract

## Request Summary

Implement the Phase 2 parser foundation: richer command grammar, structured condition and
expression parsing, and clearer user-facing parse errors. Existing Phase 1 commands must continue
to execute through the CLI -> parser -> executor -> DuckDB pipeline.

## Roadmap Phase

Phase 2: Command Language & Parser.

## Grammar

Supported general command shape:

```text
command [varlist] [if expression] [, option [option=value ...]]
```

Rules:

- Command names are case-insensitive.
- Varlist items are non-whitespace argument strings after the command and before `if`, `=`, or `,`;
  this preserves Phase 1 support for punctuated column names such as `bmi-zscore`.
- Options appear after one comma and are whitespace-separated.
- Options may be boolean flags (`detail`) or key/value pairs (`limit=10`).
- `if` introduces one expression and must not appear more than once.
- `if` expressions may appear before comma options.
- Quoted string literals are supported in expressions.
- Paths for `use` remain a single whitespace-free path argument in Phase 2.

Examples:

```text
summarize age bmi
summarize age bmi if age >= 18
summarize age bmi, detail limit=10
summarize age if sex == "F", detail
generate log_cost = log(cost)
```

## Expression Syntax

Expression parser support:

- identifiers: `age`, `cost`, `sex`
- numbers: `18`, `22.5`
- strings: `"F"`, `'M'`
- unary minus: `-cost`
- arithmetic: `+`, `-`, `*`, `/`
- comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`
- parentheses for grouping
- function calls: `log(cost)`, `sqrt(age + 1)`

Unsupported expression syntax must fail during parsing with a command-language error, not a
backend error.

## Executable Commands

The following Phase 1 commands remain executable:

### `use`

```text
use <path>
```

Loads one local `.parquet` file into the active dataset.

### `describe`

```text
describe
```

Prints active dataset structure. Varlist, `if`, and options are still invalid for executable
`describe`.

### `summarize`

```text
summarize [varlist]
```

Summarizes numeric columns exactly as in Phase 1. The parser may accept structured Phase 2 forms
for future commands, but executor support for `summarize if ...` or `summarize, detail` is not part
of this slice.

Assignment syntax is invalid for `summarize`; `summarize age = 5` must fail during parsing.

### `exit` / `quit`

Exit aliases accept no arguments, `if`, or options.

## Parsed-Only Commands

The parser should be able to represent future command-language forms such as:

```text
keep if age >= 18
generate log_cost = log(cost)
```

These are parsed for grammar coverage only. The executor should return an unsupported-command
execution error if such parsed commands are sent to it.

## Error Behavior

Parse errors should name the problem and give the smallest useful correction. Required cases:

- empty command
- unknown command
- missing `use` path
- unsupported extra arguments to `describe`, `exit`, or `quit`
- missing expression after `if`
- duplicate `if`
- malformed option syntax
- assignment syntax on commands that do not support it
- unterminated quoted string
- incomplete expression
- unsupported token in expression

## Non-Goals

- No execution for filtered summaries, `keep`, `drop`, `generate`, or `replace`.
- No persistent transformed dataset state.
- No SQL command, scripting, prompt-toolkit UX, visualization, lazy execution optimization, remote
  paths, or non-Parquet loaders.
- No full Stata compatibility.

## Acceptance Criteria

- Existing Phase 1 CLI behavior and tests continue to pass.
- Parser tests cover valid Phase 2 command, option, condition, and expression forms.
- Parser tests cover invalid Phase 2 syntax and stable user-facing error categories.
- CLI smoke tests verify malformed commands print `Error: ...`.
- Validation passes:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ruff format --check .`

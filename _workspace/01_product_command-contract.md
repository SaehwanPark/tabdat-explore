# Phase 5 CLI UX Contract

## Request Summary

Add prompt-toolkit-powered interactive shell UX while preserving existing command execution behavior.

## Roadmap Phase

Phase 5: CLI UX.

## Interactive Behavior

- Interactive `uv run tabdat` uses a `prompt_toolkit.PromptSession`.
- Batch mode with `tabdat -c ...` is unchanged and remains smoke-testable.
- Prompt text remains `tabdat> `.
- Open multiline SQL triple quotes continue with the `... ` continuation prompt until closed.
- Command history is persisted in `~/.tabdat_history`.
- Inline suggestions come from prior command history.

## Autocomplete Semantics

- At the first token, suggest executable command names: `use`, `describe`, `summarize`, `codebook`,
  `count`, `head`, `tail`, `keep`, `drop`, `select`, `rename`, `generate`, `replace`, `tabulate`,
  `collapse`, `sql`, `by`, `exit`, and `quit`.
- For command arguments that commonly accept variable names, suggest active dataset columns when an
  active dataset exists.
- For `by <vars>:` prefixes, suggest active dataset columns before `:` and command names after `:`.
- After a comma in `tabulate`, suggest `row`, `col`, and `missing`.
- After a comma in `collapse`, suggest `by(`.
- In `sql` input, suggest lightweight SQL helpers such as `select`, `from active`, `where`,
  `group by`, `order by`, and `into`.
- Before a dataset is loaded, column completions are empty.

## Highlighting Semantics

- Highlight known command names and `by`, `if`, and `into` keywords.
- Highlight numbers, strings, operators, commas, and parentheses.
- Highlighting is presentational only and does not change parsing or execution.

## Non-Goals

- No new TabDat commands.
- No changes to parser grammar, executor semantics, backend state, or formatter output.
- No semantic SQL parser or full SQL autocomplete.
- No external shell configuration, keybinding customization, or terminal theme system.

## Acceptance Criteria

- Focused tests cover command, column, option, `by`, and SQL completions.
- Focused tests cover lexer output for command and literal highlighting.
- CLI tests confirm `-c` execution remains unchanged.
- Documentation records Phase 5 as complete and notes current limitations.
- Validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`

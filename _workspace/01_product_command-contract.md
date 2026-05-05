# Phase 8 Scripting Contract

## Request Summary

Add deterministic script execution so users can rerun command sequences outside the interactive
shell.

## Command Surface

### CLI Script Entry Points

Syntax:

```text
tabdat -f analysis.td
tabdat analysis.td
```

- Both forms run a script file and exit.
- `-c/--command` command mode remains supported.
- `-c/--command` cannot be combined with `-f` or positional script execution.
- `-f` cannot be combined with positional script execution.

### `run`

Syntax:

```text
run analysis.td
```

- Runs a script from an interactive shell or from another script.
- Accepts exactly one script path.
- Relative nested `run` paths resolve from the containing script directory.
- Recursive script inclusion is rejected.

## Script Syntax

- Scripts are UTF-8 text files.
- Empty lines are ignored.
- Lines whose first non-space character is `#` are ignored.
- Each remaining line is one TabDat command, except multiline SQL:

```text
sql """
select *
from active
"""
```

- Row-level command `if` clauses keep their existing meaning.
- Script-level `if` / `else`, loops, macros, and error-control forms are not supported in this
  slice.

## Execution Behavior

- A script run uses one executor session, so commands share active dataset state.
- Script runs print deterministic metadata before command output:
  - script path
  - TabDat package version
  - Python version
- Each executed command is echoed as `. <command>` before its result.
- Plot auto-open is disabled for script execution.
- `exit` or `quit` stops the current script successfully.
- Nested `run` prints metadata for the nested script before its commands.

## Error Behavior

- Script execution fails fast on the first parse or execution error.
- Script errors are printed to stderr and include script path and starting line number.
- Failed scripts return CLI exit code `1`.
- Missing files, directories, invalid UTF-8, recursion, parse errors, and execution errors are
  script errors.

## Lazy-Mode Honesty

- `engine=polars` remains accepted but is marked experimental in docs and metadata wording.
- Lazy load validates readability and metadata through DuckDB.
- The docs identify that transformations currently materialize the active relation after the first
  lazy transformation.

## Acceptance Criteria

- Parser tests cover `run` syntax.
- Script parser tests cover comments, blank lines, multiline SQL, and unterminated multiline SQL.
- CLI tests cover `-f`, positional script execution, invalid argument combinations, and script
  failures with line numbers.
- Script execution tests cover nested `run`, relative path resolution, recursion rejection, exit,
  and deterministic mini-session output.
- Validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`

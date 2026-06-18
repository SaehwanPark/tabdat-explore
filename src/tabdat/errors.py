"""Command-level errors for TabDat.

Defines the core exception hierarchy used throughout the parsing, validation,
and execution pipeline. All exceptions meant to be caught at the CLI or interactive
shell boundary and formatted into user-friendly diagnostic messages should inherit
from TabDatError.
"""


class TabDatError(Exception):
  """Base class for all user-facing or pipeline-specific TabDat exceptions.

  Caught by the CLI, interactive shell, or script runners to prevent raw stack
  traces from leaking to the end user, instead rendering a clean error message.
  """


class ParseError(TabDatError):
  """Raised during the lexical analysis or parsing phase.

  Indicates that the user input command violates the syntax grammar or lacks
  mandatory positional/keyword options.
  """


class ExecutionError(TabDatError):
  """Base class for exceptions raised during command execution or semantic analysis.

  Indicates that the command is syntactically valid but fails validation against the
  active session state, schema, or runtime constraints.
  """


class NoActiveDatasetError(ExecutionError):
  """Raised when a dataset-dependent command is executed without a loaded active dataset.

  Commands such as `describe`, `summarize`, or `regress` require an active table
  in the session context.
  """


class UnknownVariableError(ExecutionError):
  """Raised when a command references one or more column names missing from the schema.

  Allows identifying typos in variable names during analysis.
  """


class TypeMismatchExecutionError(ExecutionError):
  """Raised when a column's data type is incompatible with the executed command.

  For example, running regression or statistical summaries on non-numeric columns.
  """


class UnknownTableError(ExecutionError):
  """Raised when a command references a named table/dataset that does not exist.

  This applies to commands managing multiple datasets or workspace frames.
  """


class ReservedNameError(ExecutionError):
  """Raised when a user attempts to define a table, variable, or scalar with a reserved name.

  Prevents collision with built-in commands, functions, or internal variables.
  """


class BackendExecutionError(ExecutionError):
  """Raised when the execution backend (e.g., DuckDB, Pandas, PyArrow) fails an operation.

  Wraps underlying system-level or query-level failures (such as database query
  cancellations, out-of-memory errors, or file read failures) to maintain pipeline contracts.
  """

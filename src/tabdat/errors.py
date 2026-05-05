"""Command-level errors for TabDat."""


class TabDatError(Exception):
  """Base class for user-facing TabDat errors."""


class ParseError(TabDatError):
  """Raised when command text cannot be parsed."""


class ExecutionError(TabDatError):
  """Raised when a parsed command cannot be executed."""


class NoActiveDatasetError(ExecutionError):
  """Raised when a command requires an active dataset but none exists."""


class UnknownVariableError(ExecutionError):
  """Raised when a command references a missing column."""


class TypeMismatchExecutionError(ExecutionError):
  """Raised when a command receives a column with an unsupported type."""


class UnknownTableError(ExecutionError):
  """Raised when a command references a missing named table."""


class ReservedNameError(ExecutionError):
  """Raised when a user-facing name is invalid or reserved."""


class BackendExecutionError(ExecutionError):
  """Raised when the backend cannot complete an operation."""

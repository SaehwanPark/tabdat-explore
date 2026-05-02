"""Command-level errors for TabDat."""


class TabDatError(Exception):
  """Base class for user-facing TabDat errors."""


class ParseError(TabDatError):
  """Raised when command text cannot be parsed."""


class ExecutionError(TabDatError):
  """Raised when a parsed command cannot be executed."""

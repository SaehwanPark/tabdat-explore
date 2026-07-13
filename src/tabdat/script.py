"""Script parsing helpers for deterministic TabDat command files."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from tabdat.errors import TabDatError

_MACRO_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MACRO_REFERENCE_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class ScriptCommand:
  text: str
  start_line: int


@dataclass(frozen=True)
class SeedDirective:
  value: int


@dataclass(frozen=True)
class LetDirective:
  name: str
  value: str


@dataclass(frozen=True)
class IfDirective:
  active: bool


@dataclass(frozen=True)
class ElseDirective:
  pass


@dataclass(frozen=True)
class EndDirective:
  pass


@dataclass(frozen=True)
class ScriptBlockState:
  start_line: int
  condition_active: bool
  in_else: bool = False

  @property
  def current_branch_active(self) -> bool:
    return not self.condition_active if self.in_else else self.condition_active


@dataclass
class ScriptContext:
  macros: dict[str, str]
  seed: int | None = None

  @classmethod
  def empty(cls) -> "ScriptContext":
    return cls(macros={})


ScriptDirective = SeedDirective | LetDirective
ControlFlowDirective = IfDirective | ElseDirective | EndDirective


class ScriptError(TabDatError):
  """Recoverable script parsing or execution error with source location."""

  def __init__(self, path: Path, line: int, message: str) -> None:
    self.path = path
    self.line = line
    self.message = message
    super().__init__(f"{path}:{line}: {message}")


def read_script(path: Path) -> tuple[ScriptCommand, ...]:
  """Read a script file from disk and parse it into structured commands.

  Args:
    path: Path to the target script file.

  Returns:
    A tuple of parsed ScriptCommand instances.

  Raises:
    ScriptError: If the file is missing, unreadable, or not valid UTF-8.
  """
  raw = b""
  try:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
  except FileNotFoundError as exc:
    raise ScriptError(path, 1, "script file not found") from exc
  except IsADirectoryError as exc:
    raise ScriptError(path, 1, "script path is a directory") from exc
  except UnicodeDecodeError as exc:
    line = raw.count(b"\n", 0, exc.start) + 1
    raise ScriptError(path, line, "script file must be UTF-8 text") from exc
  except OSError as exc:
    raise ScriptError(path, 1, f"could not read script: {exc}") from exc
  return parse_script(text, path=path)


def parse_script(text: str, *, path: Path = Path("<script>")) -> tuple[ScriptCommand, ...]:
  """Decompose a script's raw text into discrete commands.

  Ignores comments and blank lines. Properly groups multi-line SQL commands bounded
  by triple-quotes (`\"\"\"`).

  Args:
    text: The raw content of the script.
    path: The source file path (used for diagnostic error reporting).

  Returns:
    A tuple of ScriptCommand objects.

  Raises:
    ScriptError: If a multiline SQL query is left unclosed.
  """
  commands: list[ScriptCommand] = []
  pending_sql: list[str] = []
  pending_start = 0

  for line_number, raw_line in enumerate(text.splitlines(), start=1):
    stripped = raw_line.strip()

    if pending_sql:
      pending_sql.append(raw_line)
      if _has_balanced_sql_triple_quote(pending_sql):
        commands.append(ScriptCommand("\n".join(pending_sql), pending_start))
        pending_sql = []
        pending_start = 0
      continue

    if not stripped or stripped.startswith("#"):
      continue

    if _starts_multiline_sql(stripped):
      pending_sql = [raw_line]
      pending_start = line_number
      if _has_balanced_sql_triple_quote(pending_sql):
        commands.append(ScriptCommand("\n".join(pending_sql), pending_start))
        pending_sql = []
        pending_start = 0
      continue

    commands.append(ScriptCommand(raw_line, line_number))

  if pending_sql:
    raise ScriptError(path, pending_start, 'sql multiline query is missing closing """')

  return tuple(commands)


def expand_script_macros(text: str, context: ScriptContext, *, path: Path, line: int) -> str:
  """Replace macro references (prefixed with `$`) in a command text with their defined values.

  Args:
    text: The command text containing potential `$macro_name` strings.
    context: The script evaluation context containing registered macro definitions.
    path: The source file path (for error reporting).
    line: The source line number (for error reporting).

  Returns:
    The text with all macro references substituted.

  Raises:
    ScriptError: If a macro is referenced but not defined in the context.
  """

  def replacement(match: re.Match[str]) -> str:
    name = match.group(1)
    value = context.macros.get(name)
    if value is None:
      raise ScriptError(path, line, f"undefined macro: {name}")
    return value

  return _MACRO_REFERENCE_PATTERN.sub(replacement, text)


def parse_script_directive(
  text: str,
  context: ScriptContext,
  *,
  path: Path,
  line: int,
) -> ScriptDirective | None:
  """Parse a special script directive command (e.g., `let` or `seed`).

  Args:
    text: The expanded command line text.
    context: The active script evaluation context.
    path: The source file path.
    line: The source line number.

  Returns:
    A SeedDirective, LetDirective, or None if the text is not a script directive.

  Raises:
    ScriptError: If the directive has invalid arguments or syntax.
  """
  stripped = text.strip()
  command_name = stripped.split(maxsplit=1)[0].lower() if stripped else ""
  if command_name == "seed":
    return _parse_seed_directive(stripped, path=path, line=line)
  if command_name == "let":
    return _parse_let_directive(stripped, context, path=path, line=line)
  return None


def parse_control_flow_directive(
  text: str,
  *,
  path: Path,
  line: int,
) -> ControlFlowDirective | None:
  """Parse a conditional branching directive (e.g., `if`, `else`, `end`).

  Args:
    text: The expanded command line text.
    path: The source file path.
    line: The source line number.

  Returns:
    An IfDirective, ElseDirective, EndDirective, or None if not control flow.

  Raises:
    ScriptError: If syntax or structure constraints are violated.
  """
  stripped = text.strip()
  command_name, _, body = stripped.partition(" ")
  normalized = command_name.lower()
  if normalized == "if":
    condition = body.strip()
    if not condition:
      raise ScriptError(path, line, "if expects a condition")
    return IfDirective(active=evaluate_script_condition(condition, path=path, line=line))
  if normalized == "else":
    if body.strip():
      raise ScriptError(path, line, "else does not accept a condition")
    return ElseDirective()
  if normalized == "end":
    if body.strip():
      raise ScriptError(path, line, "end does not accept arguments")
    return EndDirective()
  return None


def evaluate_script_condition(condition: str, *, path: Path, line: int) -> bool:
  """Evaluate a script conditional expression to a boolean state.

  Supports basic truthy/falsy keywords (true, false, on, off, 1, 0) and simple
  equality comparisons (`==`, `!=`).

  Args:
    condition: The condition expression string to evaluate.
    path: The source file path.
    line: The source line number.

  Returns:
    True if the condition is satisfied, otherwise False.

  Raises:
    ScriptError: If the condition is syntactically invalid.
  """
  normalized = condition.strip().lower()
  if normalized in {"true", "on", "1"}:
    return True
  if normalized in {"false", "off", "0"}:
    return False

  for operator in ("==", "!="):
    left, separator, right = condition.partition(operator)
    if separator:
      left_value = left.strip()
      right_value = right.strip()
      if not left_value or not right_value:
        raise ScriptError(
          path,
          line,
          "if condition expects true/false, 1/0, on/off, ==, or !=",
        )
      return left_value == right_value if operator == "==" else left_value != right_value

  raise ScriptError(path, line, "if condition expects true/false, 1/0, on/off, ==, or !=")


def _parse_seed_directive(text: str, *, path: Path, line: int) -> SeedDirective:
  parts = text.split()
  if len(parts) != 2:
    raise ScriptError(path, line, "seed expects an integer")
  try:
    value = int(parts[1])
  except ValueError as exc:
    raise ScriptError(path, line, "seed expects an integer") from exc
  return SeedDirective(value=value)


def _parse_let_directive(
  text: str,
  context: ScriptContext,
  *,
  path: Path,
  line: int,
) -> LetDirective:
  body = text[3:].strip()
  name, separator, value = body.partition("=")
  if not separator:
    raise ScriptError(path, line, "let expects syntax: let <name> = <value>")
  name = name.strip()
  value = value.strip()
  if not name:
    raise ScriptError(path, line, "let expects syntax: let <name> = <value>")
  if not _MACRO_NAME_PATTERN.fullmatch(name):
    raise ScriptError(path, line, f"macro name must be an identifier: {name}")
  if not value:
    raise ScriptError(path, line, f"macro value cannot be empty: {name}")
  if name in context.macros:
    raise ScriptError(path, line, f"macro already defined: {name}")
  return LetDirective(name=name, value=value)


def _starts_multiline_sql(stripped_line: str) -> bool:
  parts = stripped_line.split(maxsplit=1)
  return len(parts) == 2 and parts[0].lower() == "sql" and parts[1].lstrip().startswith('"""')


def _has_balanced_sql_triple_quote(lines: Iterable[str]) -> bool:
  return "\n".join(lines).count('"""') % 2 == 0

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


@dataclass
class ScriptContext:
  macros: dict[str, str]
  seed: int | None = None

  @classmethod
  def empty(cls) -> "ScriptContext":
    return cls(macros={})


ScriptDirective = SeedDirective | LetDirective


class ScriptError(TabDatError):
  """Recoverable script parsing or execution error with source location."""

  def __init__(self, path: Path, line: int, message: str) -> None:
    self.path = path
    self.line = line
    self.message = message
    super().__init__(f"{path}:{line}: {message}")


def read_script(path: Path) -> tuple[ScriptCommand, ...]:
  try:
    text = path.read_text(encoding="utf-8")
  except FileNotFoundError as exc:
    raise ScriptError(path, 1, "script file not found") from exc
  except IsADirectoryError as exc:
    raise ScriptError(path, 1, "script path is a directory") from exc
  except UnicodeDecodeError as exc:
    raise ScriptError(path, exc.start + 1, "script file must be UTF-8 text") from exc
  except OSError as exc:
    raise ScriptError(path, 1, f"could not read script: {exc}") from exc
  return parse_script(text, path=path)


def parse_script(text: str, *, path: Path = Path("<script>")) -> tuple[ScriptCommand, ...]:
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
  stripped = text.strip()
  command_name = stripped.split(maxsplit=1)[0].lower() if stripped else ""
  if command_name == "seed":
    return _parse_seed_directive(stripped, path=path, line=line)
  if command_name == "let":
    return _parse_let_directive(stripped, context, path=path, line=line)
  return None


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

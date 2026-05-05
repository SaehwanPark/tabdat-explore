"""Script parsing helpers for deterministic TabDat command files."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from tabdat.errors import TabDatError


@dataclass(frozen=True)
class ScriptCommand:
  text: str
  start_line: int


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


def _starts_multiline_sql(stripped_line: str) -> bool:
  parts = stripped_line.split(maxsplit=1)
  return len(parts) == 2 and parts[0].lower() == "sql" and parts[1].lstrip().startswith('"""')


def _has_balanced_sql_triple_quote(lines: Iterable[str]) -> bool:
  return "\n".join(lines).count('"""') % 2 == 0

"""Command-line entry point for TabDat."""

import argparse
import sys
from collections.abc import Callable, Sequence
from enum import Enum, auto

from tabdat.errors import TabDatError
from tabdat.executor import Executor
from tabdat.formatter import format_result
from tabdat.models import ExitCommand
from tabdat.parser import parse_command
from tabdat.shell import create_prompt_session


class _RunStatus(Enum):
  CONTINUE = auto()
  STOP = auto()
  ERROR = auto()


def main(argv: Sequence[str] | None = None) -> int:
  parser = argparse.ArgumentParser(prog="tabdat")
  parser.add_argument("-c", "--command", action="append", help="run a command and exit")
  args = parser.parse_args(argv)

  executor = Executor()
  try:
    if args.command:
      return _run_commands(args.command, executor)
    return _run_shell(executor)
  finally:
    executor.close()


def _run_commands(commands: Sequence[str], executor: Executor) -> int:
  for command_text in commands:
    status = _run_one(command_text, executor)
    if status is _RunStatus.ERROR:
      return 1
    if status is _RunStatus.STOP:
      break
  return 0


def _run_shell(executor: Executor) -> int:
  session = create_prompt_session(executor)
  while True:
    try:
      command_text = session.prompt("tabdat> ")
      command_text = _read_multiline_sql(command_text, session.prompt)
    except EOFError:
      print()
      return 0

    if _run_one(command_text, executor) is _RunStatus.STOP:
      return 0


def _run_one(command_text: str, executor: Executor) -> _RunStatus:
  try:
    command = parse_command(command_text)
    if isinstance(command, ExitCommand):
      return _RunStatus.STOP
    result = executor.execute(command)
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    return _RunStatus.ERROR

  if result is not None:
    print(format_result(result))
  return _RunStatus.CONTINUE


def _read_multiline_sql(
  command_text: str,
  read_continuation: Callable[[str], str] = input,
) -> str:
  if not _has_open_sql_triple_quote(command_text):
    return command_text

  lines = [command_text]
  while True:
    continuation = read_continuation("... ")
    lines.append(continuation)
    joined = "\n".join(lines)
    if not _has_open_sql_triple_quote(joined):
      return joined


def _has_open_sql_triple_quote(command_text: str) -> bool:
  stripped = command_text.lstrip()
  parts = stripped.split(maxsplit=1)
  return (
    len(parts) == 2
    and parts[0].lower() == "sql"
    and parts[1].lstrip().startswith('"""')
    and stripped.count('"""') % 2 == 1
  )


if __name__ == "__main__":
  raise SystemExit(main())

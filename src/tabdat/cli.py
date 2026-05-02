"""Command-line entry point for TabDat."""

import argparse
import sys
from collections.abc import Sequence

from tabdat.errors import TabDatError
from tabdat.executor import Executor
from tabdat.formatter import format_result
from tabdat.models import ExitCommand
from tabdat.parser import parse_command


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
    if not _run_one(command_text, executor):
      break
  return 0


def _run_shell(executor: Executor) -> int:
  while True:
    try:
      command_text = input("tabdat> ")
    except EOFError:
      print()
      return 0

    if not _run_one(command_text, executor):
      return 0


def _run_one(command_text: str, executor: Executor) -> bool:
  try:
    command = parse_command(command_text)
    if isinstance(command, ExitCommand):
      return False
    result = executor.execute(command)
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    return True

  if result is not None:
    print(format_result(result))
  return True


if __name__ == "__main__":
  raise SystemExit(main())

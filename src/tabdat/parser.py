"""Minimal Phase 1 command parser."""

from pathlib import Path

from tabdat.errors import ParseError
from tabdat.models import Command, DescribeCommand, ExitCommand, SummarizeCommand, UseCommand


def parse_command(text: str) -> Command:
  parts = text.strip().split()
  if not parts:
    raise ParseError("empty command")

  command, *args = parts
  command = command.lower()

  if command == "use":
    if len(args) != 1:
      raise ParseError("use expects exactly one path: use <path>")
    return UseCommand(path=Path(args[0]))

  if command == "describe":
    if args:
      raise ParseError("describe does not accept arguments in Phase 1")
    return DescribeCommand()

  if command == "summarize":
    return SummarizeCommand(variables=tuple(args))

  if command in {"exit", "quit"}:
    if args:
      raise ParseError(f"{command} does not accept arguments")
    return ExitCommand()

  raise ParseError(f"unknown command: {command}")

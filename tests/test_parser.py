from pathlib import Path

import pytest

from tabdat.errors import ParseError
from tabdat.models import DescribeCommand, ExitCommand, SummarizeCommand, UseCommand
from tabdat.parser import parse_command


def test_parse_use_command() -> None:
  assert parse_command("use data.parquet") == UseCommand(Path("data.parquet"))


def test_parse_describe_command() -> None:
  assert parse_command("describe") == DescribeCommand()


def test_parse_summarize_command_with_variables() -> None:
  assert parse_command("summarize age bmi") == SummarizeCommand(("age", "bmi"))


def test_parse_summarize_command_without_variables() -> None:
  assert parse_command("summarize") == SummarizeCommand(())


def test_parse_exit_aliases() -> None:
  assert parse_command("exit") == ExitCommand()
  assert parse_command("quit") == ExitCommand()


@pytest.mark.parametrize(
  "text",
  [
    "",
    "use",
    "use one.parquet two.parquet",
    "describe age",
    "exit now",
    "unknown",
  ],
)
def test_parse_invalid_commands(text: str) -> None:
  with pytest.raises(ParseError):
    parse_command(text)

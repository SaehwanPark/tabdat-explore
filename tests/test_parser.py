from pathlib import Path

import pytest

from tabdat.errors import ParseError
from tabdat.models import (
  BinaryExpression,
  CommandOption,
  DescribeCommand,
  ExitCommand,
  FunctionCallExpression,
  IdentifierExpression,
  NumberExpression,
  ParsedCommand,
  StringExpression,
  SummarizeCommand,
  UseCommand,
)
from tabdat.parser import parse_command, parse_expression


def test_parse_use_command() -> None:
  assert parse_command("use data.parquet") == UseCommand(Path("data.parquet"))


def test_parse_describe_command() -> None:
  assert parse_command("describe") == DescribeCommand()


def test_parse_summarize_command_with_variables() -> None:
  assert parse_command("summarize age bmi") == SummarizeCommand(("age", "bmi"))


def test_parse_summarize_command_without_variables() -> None:
  assert parse_command("summarize") == SummarizeCommand(())


def test_parse_summarize_with_if_as_structured_phase_2_command() -> None:
  assert parse_command("summarize age bmi if age >= 18") == ParsedCommand(
    name="summarize",
    arguments=("age", "bmi"),
    condition=BinaryExpression(
      left=IdentifierExpression("age"),
      operator=">=",
      right=NumberExpression(18),
    ),
  )


def test_parse_summarize_with_options_as_structured_phase_2_command() -> None:
  assert parse_command("summarize age bmi, detail limit=10") == ParsedCommand(
    name="summarize",
    arguments=("age", "bmi"),
    options=(
      CommandOption("detail", True),
      CommandOption("limit", 10),
    ),
  )


def test_parse_condition_and_options() -> None:
  assert parse_command('summarize age if sex == "F", detail') == ParsedCommand(
    name="summarize",
    arguments=("age",),
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
    options=(CommandOption("detail", True),),
  )


def test_parse_future_keep_command() -> None:
  assert parse_command("keep if age >= 18") == ParsedCommand(
    name="keep",
    condition=BinaryExpression(
      left=IdentifierExpression("age"),
      operator=">=",
      right=NumberExpression(18),
    ),
  )


def test_parse_future_generate_command() -> None:
  assert parse_command("generate log_cost = log(cost)") == ParsedCommand(
    name="generate",
    arguments=("log_cost",),
    expression=FunctionCallExpression(
      name="log",
      arguments=(IdentifierExpression("cost"),),
    ),
  )


def test_parse_expression_with_precedence_and_function_call() -> None:
  assert parse_expression("sqrt(age + 1) >= 5") == BinaryExpression(
    left=FunctionCallExpression(
      name="sqrt",
      arguments=(
        BinaryExpression(
          left=IdentifierExpression("age"),
          operator="+",
          right=NumberExpression(1),
        ),
      ),
    ),
    operator=">=",
    right=NumberExpression(5),
  )


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
    "describe if age > 18",
    "exit now",
    "unknown",
    "summarize age if",
    "summarize age if age >=",
    "summarize age if if age > 18",
    "summarize age if age > 18 if bmi > 20",
    "summarize age,",
    "summarize age, limit=",
    "summarize age, limit 10",
    'summarize age if sex == "F',
    "summarize age if age $ 18",
  ],
)
def test_parse_invalid_commands(text: str) -> None:
  with pytest.raises(ParseError):
    parse_command(text)

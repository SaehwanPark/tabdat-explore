"""Focused coverage for the read-only row assertion quality gate."""

import json
from pathlib import Path
from typing import Literal

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import (
  ExecutionError,
  ParseError,
  TypeMismatchExecutionError,
  UnknownVariableError,
)
from tabdat.executor import Executor
from tabdat.models import (
  AssertCommand,
  AssertResult,
  BinaryExpression,
  Expression,
  IdentifierExpression,
  NumberExpression,
  UseCommand,
)
from tabdat.parser import parse_command


def _assert_expression(text: str) -> Expression:
  command = parse_command(text)
  assert isinstance(command, AssertCommand)
  return command.expression


def _write_empty_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      "copy (select cast(null as integer) as value where false) to ? (format parquet)",
      [str(path)],
    )
  finally:
    connection.close()


def test_parse_assert_commands() -> None:
  assert parse_command("assert age > 0") == AssertCommand(
    expression=BinaryExpression(
      left=IdentifierExpression(name="age"),
      operator=">",
      right=NumberExpression(value=0),
    )
  )
  assert parse_command("assert `age` >= 18") == AssertCommand(
    expression=BinaryExpression(
      left=IdentifierExpression(name="age"),
      operator=">=",
      right=NumberExpression(value=18),
    )
  )

  with pytest.raises(ParseError, match="assert expects a boolean expression"):
    parse_command("assert")
  with pytest.raises(ParseError, match="assert does not accept options"):
    parse_command("assert age > 0, strict")
  with pytest.raises(ParseError, match="assert does not accept if clauses"):
    parse_command("assert age > 0 if sex == 'F'")
  with pytest.raises(ParseError, match="assert does not accept assignment syntax"):
    parse_command("assert age = 0")


def test_assert_passes_and_preserves_active_state(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    result = executor.execute(AssertCommand(_assert_expression("assert age > 0")))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, AssertResult)
  assert result.checked == 3
  assert result.failed == 0
  assert before == after


def test_assert_fails_on_false_or_missing_rows_without_state_change(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    with pytest.raises(ExecutionError, match="assertion failed: 1 of 3 rows failed"):
      executor.execute(AssertCommand(_assert_expression("assert cost > 0")))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after
  assert executor.state.last_operation == "use"


def test_assert_rejects_non_boolean_and_unknown_expressions(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(TypeMismatchExecutionError, match="predicate requires boolean expression"):
      executor.execute(AssertCommand(_assert_expression("assert age")))
    with pytest.raises(UnknownVariableError, match="expression.*missing"):
      executor.execute(AssertCommand(_assert_expression("assert missing > 0")))
  finally:
    executor.close()


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_assert_supports_eager_and_lazy_engines(
  sample_parquet: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(sample_parquet))
    else:
      executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(AssertCommand(_assert_expression("assert age >= 0")))
    active = executor.state.active_dataset
    polars_lazy = executor.backend.is_polars_lazy_active()
  finally:
    executor.close()

  assert isinstance(result, AssertResult)
  assert result == AssertResult(checked=3, failed=0)
  assert active is not None
  if lazy_engine is None:
    assert active.execution_mode == "eager"
  else:
    assert active.execution_mode == "lazy"
    assert active.lazy_engine == lazy_engine
    assert active.row_count is None
  assert polars_lazy == (lazy_engine == "polars")


def test_assert_empty_dataset_passes(tmp_path: Path) -> None:
  path = tmp_path / "empty.parquet"
  _write_empty_fixture(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(AssertCommand(_assert_expression("assert value == null")))
  finally:
    executor.close()

  assert result == AssertResult(checked=0, failed=0)


def test_cli_assert_human_json_and_failure(
  sample_parquet: Path, capsys: pytest.CaptureFixture[str]
) -> None:
  exit_code = main(["-c", f"use {sample_parquet}", "-c", "assert age > 0"])
  captured = capsys.readouterr()

  assert exit_code == 0
  assert captured.out.endswith("assertion passed: 3 rows\n")
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {sample_parquet}", "-c", "assert age > 0"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]

  assert json_exit_code == 0
  assert envelopes[-1] == {
    "data": {"checked": 3, "failed": 0},
    "result_type": "AssertResult",
    "schema_version": 1,
  }
  assert json_captured.err == ""

  failure_exit_code = main(["-c", f"use {sample_parquet}", "-c", "assert cost > 0"])
  failure_captured = capsys.readouterr()

  assert failure_exit_code == 1
  assert "assertion passed" not in failure_captured.out
  assert "assertion failed: 1 of 3 rows failed" in failure_captured.err

  json_failure_exit_code = main(["--json", "-c", f"use {sample_parquet}", "-c", "assert cost > 0"])
  json_failure_captured = capsys.readouterr()
  json_failure = json.loads(json_failure_captured.out.splitlines()[-1])

  assert json_failure_exit_code == 1
  assert json_failure["error"]["type"] == "ExecutionError"
  assert json_failure["error"]["message"] == "assertion failed: 1 of 3 rows failed"
  assert json_failure_captured.err


def test_cli_assert_requires_active_dataset(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", "assert age > 0"])
  captured = capsys.readouterr()

  assert exit_code != 0
  assert "active dataset" in captured.err.lower()

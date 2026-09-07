"""Focused coverage for the null-missingness report."""

import json
from pathlib import Path

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import ParseError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.models import MissingCommand, MissingResult, UseCommand
from tabdat.parser import parse_command


def test_parse_missing_commands() -> None:
  assert parse_command("missing") == MissingCommand(variables=())
  assert parse_command("missing cost age") == MissingCommand(variables=("cost", "age"))


def test_parse_missing_rejects_options_conditions_and_assignment() -> None:
  with pytest.raises(ParseError, match="missing does not accept if clauses or options"):
    parse_command("missing age, foo")
  with pytest.raises(ParseError, match="missing does not accept if clauses or options"):
    parse_command("missing age if age > 0")
  with pytest.raises(ParseError, match="assignment"):
    parse_command("missing = age")


def test_missing_report_preserves_schema_and_requested_order(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    all_columns = executor.execute(MissingCommand(variables=()))
    requested = executor.execute(MissingCommand(variables=("cost", "age")))
  finally:
    executor.close()

  assert isinstance(all_columns, MissingResult)
  assert [(row.variable, row.missing, row.nonmissing) for row in all_columns.rows] == [
    ("age", 0, 3),
    ("bmi", 0, 3),
    ("sex", 0, 3),
    ("cost", 1, 2),
  ]
  assert all_columns.rows[-1].missing_percent == pytest.approx(100 / 3)
  assert isinstance(requested, MissingResult)
  assert tuple(row.variable for row in requested.rows) == ("cost", "age")


def test_missing_report_rejects_unknown_variable_without_state_change(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    with pytest.raises(UnknownVariableError, match="missing"):
      executor.execute(MissingCommand(variables=("missing",)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after


def test_missing_report_empty_dataset_returns_zero_percent(tmp_path: Path) -> None:
  path = tmp_path / "empty.parquet"
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      "copy (select cast(null as integer) as value where false) to ? (format parquet)",
      [str(path)],
    )
  finally:
    connection.close()

  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(MissingCommand(variables=()))
  finally:
    executor.close()

  assert isinstance(result, MissingResult)
  assert result.rows[0].total == 0
  assert result.rows[0].missing == 0
  assert result.rows[0].missing_percent == 0.0


@pytest.mark.parametrize("lazy_engine", ["duckdb", "polars"])
def test_missing_report_preserves_lazy_execution(sample_parquet: Path, lazy_engine: str) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(MissingCommand(variables=("cost",)))
    active = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, MissingResult)
  assert result.rows[0].missing == 1
  assert active is not None
  assert active.execution_mode == "lazy"
  assert active.lazy_engine == lazy_engine
  assert active.row_count is None


def test_cli_missing_human_and_json(
  sample_parquet: Path, capsys: pytest.CaptureFixture[str]
) -> None:
  exit_code = main(["-c", f"use {sample_parquet}", "-c", "missing cost"])
  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Variable" in captured.out
  assert "cost" in captured.out
  assert "Missing %" in captured.out
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {sample_parquet}", "-c", "missing cost"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]

  assert json_exit_code == 0
  assert envelopes[-1]["result_type"] == "MissingResult"
  assert envelopes[-1]["data"]["rows"][0]["missing"] == 1
  assert json_captured.err == ""


def test_cli_missing_requires_active_dataset(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", "missing"])
  captured = capsys.readouterr()

  assert exit_code != 0
  assert "active dataset" in captured.err.lower()

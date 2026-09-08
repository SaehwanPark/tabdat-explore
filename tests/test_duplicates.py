"""Focused coverage for the read-only duplicate-key quality report."""

import json
from pathlib import Path
from typing import Literal

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import ParseError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.models import DuplicatesCommand, DuplicatesResult, UseCommand
from tabdat.parser import parse_command


def _write_duplicate_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      """
      copy (
        select * from (
          values
            (1, 'a'),
            (1, 'a'),
            (2, 'b'),
            (null, 'c'),
            (null, 'c')
        ) as duplicate_data(id, label)
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()


def _write_empty_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      "copy (select cast(null as integer) as id where false) to ? (format parquet)",
      [str(path)],
    )
  finally:
    connection.close()


def _write_alias_collision_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      """
      copy (
        select * from (
          values (1), (1), (2)
        ) as duplicate_data("__tabdat_duplicate_count")
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()


def test_parse_duplicates_forms() -> None:
  assert parse_command("duplicates") == DuplicatesCommand(variables=())
  assert parse_command("duplicates report id") == DuplicatesCommand(variables=("id",))
  assert parse_command("duplicates id label") == DuplicatesCommand(variables=("id", "label"))
  assert parse_command("duplicates `report`") == DuplicatesCommand(variables=("report",))

  with pytest.raises(ParseError, match="duplicates does not accept if clauses or options"):
    parse_command("duplicates id, missing")
  with pytest.raises(ParseError, match="duplicates does not accept if clauses or options"):
    parse_command("duplicates id if id > 0")
  with pytest.raises(ParseError, match="assignment"):
    parse_command("duplicates id = other")


def test_duplicates_report_counts_requested_keys_and_preserves_state(tmp_path: Path) -> None:
  path = tmp_path / "duplicates.parquet"
  _write_duplicate_fixture(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    before = executor.state.active_dataset
    result = executor.execute(DuplicatesCommand(variables=("id",)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, DuplicatesResult)
  assert result == DuplicatesResult(
    variables=("id",),
    total_rows=5,
    unique_groups=3,
    duplicate_groups=2,
    duplicate_rows=4,
    extra_rows=2,
    max_copies=2,
  )
  assert before == after
  assert executor.state.last_operation == "duplicates"


def test_duplicates_default_key_and_no_duplicates(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(DuplicatesCommand(variables=()))
  finally:
    executor.close()

  assert result == DuplicatesResult(
    variables=("age", "bmi", "sex", "cost"),
    total_rows=3,
    unique_groups=3,
    duplicate_groups=0,
    duplicate_rows=0,
    extra_rows=0,
    max_copies=1,
  )


def test_duplicates_empty_dataset_returns_zero_counts(tmp_path: Path) -> None:
  path = tmp_path / "empty.parquet"
  _write_empty_fixture(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(DuplicatesCommand(variables=()))
  finally:
    executor.close()

  assert result == DuplicatesResult(
    variables=("id",),
    total_rows=0,
    unique_groups=0,
    duplicate_groups=0,
    duplicate_rows=0,
    extra_rows=0,
    max_copies=0,
  )


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_duplicates_handles_internal_count_alias_collision(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "duplicates_alias_collision.parquet"
  _write_alias_collision_fixture(path)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(DuplicatesCommand(variables=("__tabdat_duplicate_count",)))
  finally:
    executor.close()

  assert result == DuplicatesResult(
    variables=("__tabdat_duplicate_count",),
    total_rows=3,
    unique_groups=2,
    duplicate_groups=1,
    duplicate_rows=2,
    extra_rows=1,
    max_copies=2,
  )


def test_duplicates_unknown_variable_preserves_state(tmp_path: Path) -> None:
  path = tmp_path / "duplicates.parquet"
  _write_duplicate_fixture(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    before = executor.state.active_dataset
    with pytest.raises(UnknownVariableError, match="duplicates unknown variable"):
      executor.execute(DuplicatesCommand(variables=("missing",)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after
  assert executor.state.last_operation == "use"


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_duplicates_preserves_eager_and_lazy_execution(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "duplicates.parquet"
  _write_duplicate_fixture(path)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(DuplicatesCommand(variables=("id",)))
    active = executor.state.active_dataset
    polars_lazy = executor.backend.is_polars_lazy_active()
  finally:
    executor.close()

  assert isinstance(result, DuplicatesResult)
  assert result.duplicate_groups == 2
  assert active is not None
  if lazy_engine is None:
    assert active.execution_mode == "eager"
    assert polars_lazy is False
  else:
    assert active.execution_mode == "lazy"
    assert active.lazy_engine == lazy_engine
    assert active.row_count is None
    assert polars_lazy == (lazy_engine == "polars")


def test_cli_duplicates_human_and_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  path = tmp_path / "duplicates.parquet"
  _write_duplicate_fixture(path)

  exit_code = main(["-c", f"use {path}", "-c", "duplicates report id"])
  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Duplicates report" in captured.out
  assert "Duplicate groups: 2" in captured.out
  assert "Extra duplicate rows: 2" in captured.out
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {path}", "-c", "duplicates id"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]

  assert json_exit_code == 0
  assert envelopes[-1] == {
    "data": {
      "duplicate_groups": 2,
      "duplicate_rows": 4,
      "extra_rows": 2,
      "max_copies": 2,
      "total_rows": 5,
      "unique_groups": 3,
      "variables": ["id"],
    },
    "result_type": "DuplicatesResult",
    "schema_version": 1,
  }
  assert json_captured.err == ""


def test_cli_duplicates_requires_active_dataset(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", "duplicates"])
  captured = capsys.readouterr()

  assert exit_code != 0
  assert "active dataset" in captured.err.lower()


def test_cli_duplicates_help_and_schema(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["--json", "--describe-command", "duplicates"])
  captured = capsys.readouterr()
  envelope = json.loads(captured.out)

  assert exit_code == 0
  assert envelope["data"]["syntax"] == "duplicates [report] [varlist]"
  assert envelope["data"]["help_topic"] == "duplicates"

  help_exit_code = main(["-c", "help duplicates"])
  help_captured = capsys.readouterr()
  assert help_exit_code == 0
  assert "duplicates [report] [varlist]" in help_captured.out

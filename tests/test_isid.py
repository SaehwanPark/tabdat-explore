"""Focused coverage for read-only key-uniqueness checks."""

import json
from pathlib import Path
from typing import Literal

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import ExecutionError, ParseError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.models import IsidCommand, IsidResult, UseCommand
from tabdat.parser import parse_command


def _write_isid_fixture(
  path: Path,
  *,
  duplicate_missing: bool,
  duplicate_nonmissing: bool = False,
) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    rows = (
      "(1, 1, 'a', 1), (1, 2, 'b', 2), (2, 1, 'c', 3), "
      "(cast(null as integer), 1, 'd', 4), (cast(null as integer), 2, 'e', 5)"
    )
    if duplicate_missing:
      rows = rows.replace(
        "(cast(null as integer), 2, 'e', 5)",
        "(cast(null as integer), 1, 'e', 5)",
      )
    if duplicate_nonmissing:
      rows = rows.replace("(1, 2, 'b', 2)", "(1, 1, 'b', 2)")
    connection.execute(
      f"""
      copy (
        select * from (
          values {rows}
        ) as key_data(patient_id, visit, status, row_id)
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
      """
      copy (
        select cast(null as integer) as patient_id, cast(null as integer) as visit
        where false
      ) to ? (format parquet)
      """,
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
          values (1, 10), (2, 20)
        ) as key_data("__tabdat_isid_count", visit)
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()


def test_parse_isid_forms() -> None:
  assert parse_command("isid patient_id visit") == IsidCommand(variables=("patient_id", "visit"))
  assert parse_command("isid `patient_id` visit, missok") == IsidCommand(
    variables=("patient_id", "visit"),
    missok=True,
  )

  with pytest.raises(ParseError, match="isid expects at least one key variable"):
    parse_command("isid")
  with pytest.raises(ParseError, match="isid only accepts"):
    parse_command("isid patient_id if visit > 0")
  with pytest.raises(ParseError, match="unsupported option: report"):
    parse_command("isid patient_id, report")
  with pytest.raises(ParseError, match="does not accept a value"):
    parse_command("isid patient_id, missok(true)")


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_isid_accepts_unique_composite_keys_and_missok(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "isid_unique.parquet"
  _write_isid_fixture(path, duplicate_missing=False)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    before = executor.state.active_dataset
    result = executor.execute(IsidCommand(variables=("patient_id", "visit"), missok=True))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert result == IsidResult(
    variables=("patient_id", "visit"),
    total_rows=5,
    unique_groups=5,
    missing_key_rows=2,
    missok=True,
  )
  assert before == after
  assert executor.state.last_operation == "isid"
  if lazy_engine == "polars":
    assert after is not None
    assert after.execution_mode == "lazy"
    assert after.lazy_engine == "polars"
    assert after.row_count is None


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_isid_rejects_missing_keys_without_missok_and_preserves_state(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "isid_missing.parquet"
  _write_isid_fixture(path, duplicate_missing=False)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    before = executor.state.active_dataset
    with pytest.raises(ExecutionError, match="2 rows have missing key values"):
      executor.execute(IsidCommand(variables=("patient_id", "visit")))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after
  assert executor.state.last_operation == "use"


def test_isid_rejects_duplicate_nonmissing_key(tmp_path: Path) -> None:
  path = tmp_path / "isid_duplicate_nonmissing.parquet"
  _write_isid_fixture(path, duplicate_missing=False, duplicate_nonmissing=True)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    with pytest.raises(ExecutionError, match="2 rows are in 1 duplicate key groups"):
      executor.execute(IsidCommand(variables=("patient_id", "visit"), missok=True))
  finally:
    executor.close()


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_isid_rejects_duplicate_keys_even_with_missok(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "isid_duplicate.parquet"
  _write_isid_fixture(path, duplicate_missing=True)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    with pytest.raises(ExecutionError, match="2 rows are in 1 duplicate key groups"):
      executor.execute(IsidCommand(variables=("patient_id", "visit"), missok=True))
  finally:
    executor.close()


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_isid_empty_dataset_passes(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "isid_empty.parquet"
  _write_empty_fixture(path)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(IsidCommand(variables=("patient_id", "visit")))
  finally:
    executor.close()

  assert result == IsidResult(
    variables=("patient_id", "visit"),
    total_rows=0,
    unique_groups=0,
    missing_key_rows=0,
    missok=False,
  )


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_isid_handles_internal_count_alias_collision(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "isid_alias_collision.parquet"
  _write_alias_collision_fixture(path)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(IsidCommand(variables=("__tabdat_isid_count", "visit"), missok=False))
  finally:
    executor.close()

  assert result == IsidResult(
    variables=("__tabdat_isid_count", "visit"),
    total_rows=2,
    unique_groups=2,
    missing_key_rows=0,
    missok=False,
  )


def test_isid_unknown_variable_is_atomic(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    with pytest.raises(UnknownVariableError, match="isid unknown variable"):
      executor.execute(IsidCommand(variables=("missing_key",)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after
  assert executor.state.last_operation == "use"


def test_cli_isid_human_and_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  path = tmp_path / "isid_cli.parquet"
  _write_isid_fixture(path, duplicate_missing=False)

  exit_code = main(["-c", f"use {path}", "-c", "isid patient_id visit, missok"])
  captured = capsys.readouterr()
  assert exit_code == 0
  assert "isid passed" in captured.out
  assert "Missing keys allowed: yes" in captured.out
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {path}", "-c", "isid patient_id visit, missok"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]
  assert json_exit_code == 0
  assert envelopes[-1]["result_type"] == "IsidResult"
  assert envelopes[-1]["data"] == {
    "variables": ["patient_id", "visit"],
    "total_rows": 5,
    "unique_groups": 5,
    "missing_key_rows": 2,
    "missok": True,
  }
  assert json_captured.err == ""


def test_cli_isid_failure_schema_help_and_no_active(
  tmp_path: Path,
  capsys: pytest.CaptureFixture[str],
) -> None:
  path = tmp_path / "isid_failure.parquet"
  _write_isid_fixture(path, duplicate_missing=True)

  failure_exit_code = main(["-c", f"use {path}", "-c", "isid patient_id visit, missok"])
  failure_captured = capsys.readouterr()
  assert failure_exit_code != 0
  assert "duplicate key groups" in failure_captured.err

  schema_exit_code = main(["--json", "--describe-command", "isid"])
  schema_captured = capsys.readouterr()
  schema = json.loads(schema_captured.out)
  assert schema_exit_code == 0
  assert schema["data"] == {
    "arguments": [{"name": "variables", "required": True}],
    "help_topic": "isid",
    "name": "isid",
    "options": [{"name": "missok", "required": False}],
    "syntax": "isid varlist [, missok]",
  }

  help_exit_code = main(["-c", "help isid"])
  help_captured = capsys.readouterr()
  assert help_exit_code == 0
  assert "isid varlist [, missok]" in help_captured.out

  no_active_exit_code = main(["-c", "isid patient_id"])
  no_active_captured = capsys.readouterr()
  assert no_active_exit_code != 0
  assert "active dataset" in no_active_captured.err.lower()

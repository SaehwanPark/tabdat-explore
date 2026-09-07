"""Focused coverage for stable active-row sorting."""

import json
from pathlib import Path

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import ParseError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.models import (
  HeadCommand,
  LabelCommand,
  PanelCommand,
  SortCommand,
  TransformResult,
  UseCommand,
)
from tabdat.parser import parse_command


def _write_sort_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      """
      copy (
        select * from (
          values
            (2, 'b', true, 1),
            (1, 'a', false, 2),
            (1, 'a', true, 3),
            (cast(null as integer), 'a', false, 4)
        ) as rows(group_id, label, flag, row_id)
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()


def test_parse_sort_commands() -> None:
  assert parse_command("sort group_id label") == SortCommand(variables=("group_id", "label"))

  with pytest.raises(ParseError, match="sort expects at least one variable"):
    parse_command("sort")
  with pytest.raises(ParseError, match="sort only accepts a variable list"):
    parse_command("sort group_id, stable")
  with pytest.raises(ParseError, match="sort only accepts a variable list"):
    parse_command("sort group_id if group_id > 0")


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_sort_is_native_stable_and_nulls_last(tmp_path: Path, lazy_engine: str | None) -> None:
  path = tmp_path / "sort.parquet"
  _write_sort_fixture(path)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(SortCommand(variables=("group_id", "label")))
    preview = executor.execute(HeadCommand(limit=10))
    active = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.message == "Sorted by: group_id label"
  assert preview is not None
  assert preview.rows == (
    (1, "a", False, 2),
    (1, "a", True, 3),
    (2, "b", True, 1),
    (None, "a", False, 4),
  )
  assert active is not None
  if lazy_engine == "polars":
    assert active.execution_mode == "lazy"
    assert active.lazy_engine == "polars"
    assert active.row_count is None


def test_sort_preserves_labels_and_panel_metadata(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="variable", variable="age", text="Age"))
    executor.execute(PanelCommand(action="set", id_variable="sex", time_variable="age"))
    executor.execute(SortCommand(variables=("cost",)))
    active = executor.state.active_dataset
  finally:
    executor.close()

  assert active is not None
  assert active.label_metadata is not None
  assert active.label_metadata.variable_labels == (("age", "Age"),)
  assert active.panel_metadata is not None
  assert active.panel_metadata.id_variable == "sex"
  assert active.panel_metadata.time_variable == "age"


def test_sort_rejects_unknown_variable_without_state_change(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    with pytest.raises(UnknownVariableError, match="missing"):
      executor.execute(SortCommand(variables=("missing",)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after


def test_cli_sort_human_and_json(sample_parquet: Path, capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", f"use {sample_parquet}", "-c", "sort cost"])
  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Sorted by: cost" in captured.out
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {sample_parquet}", "-c", "sort cost"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]

  assert json_exit_code == 0
  assert envelopes[-1]["result_type"] == "TransformResult"
  assert envelopes[-1]["data"]["message"] == "Sorted by: cost"
  assert json_captured.err == ""

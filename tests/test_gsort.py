"""Focused coverage for stable mixed-direction row sorting."""

import json
from pathlib import Path
from typing import Literal

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import ParseError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.models import (
  GsortCommand,
  HeadCommand,
  LabelCommand,
  PanelCommand,
  SortKey,
  TransformResult,
  UseCommand,
)
from tabdat.parser import parse_command


def _write_gsort_fixture(path: Path) -> None:
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


def test_parse_gsort_direction_forms() -> None:
  assert parse_command("gsort group_id -label") == GsortCommand(
    keys=(SortKey("group_id"), SortKey("label", descending=True))
  )
  assert parse_command("gsort +group_id -label") == GsortCommand(
    keys=(SortKey("group_id"), SortKey("label", descending=True))
  )
  assert parse_command("gsort `-score`") == GsortCommand(keys=(SortKey("-score"),))

  with pytest.raises(ParseError, match="gsort expects at least one variable"):
    parse_command("gsort")
  with pytest.raises(ParseError, match="gsort only accepts a signed variable list"):
    parse_command("gsort group_id, stable")
  with pytest.raises(ParseError, match="gsort only accepts a signed variable list"):
    parse_command("gsort group_id if group_id > 0")
  with pytest.raises(ParseError, match="at most one"):
    parse_command("gsort --group_id")
  with pytest.raises(ParseError, match="expects a variable after"):
    parse_command("gsort -")


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_gsort_is_stable_mixed_direction_and_nulls_last(
  tmp_path: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  path = tmp_path / "gsort.parquet"
  _write_gsort_fixture(path)
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(path))
    else:
      executor.execute(UseCommand(path, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(
      GsortCommand(keys=(SortKey("group_id", descending=True), SortKey("label")))
    )
    preview = executor.execute(HeadCommand(limit=10))
    active = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.message == "Sorted by: -group_id +label"
  assert preview is not None
  assert preview.rows == (
    (2, "b", True, 1),
    (1, "a", False, 2),
    (1, "a", True, 3),
    (None, "a", False, 4),
  )
  assert active is not None
  if lazy_engine == "polars":
    assert active.execution_mode == "lazy"
    assert active.lazy_engine == "polars"
    assert active.row_count is None


def test_gsort_rejects_unknown_variable_without_state_change(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    with pytest.raises(UnknownVariableError, match="gsort unknown variable"):
      executor.execute(GsortCommand(keys=(SortKey("missing", descending=True),)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before == after
  assert executor.state.last_operation == "use"


def test_gsort_preserves_labels_and_panel_metadata(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="variable", variable="age", text="Age"))
    executor.execute(PanelCommand(action="set", id_variable="sex", time_variable="age"))
    executor.execute(GsortCommand(keys=(SortKey("cost", descending=True),)))
    active = executor.state.active_dataset
  finally:
    executor.close()

  assert active is not None
  assert active.label_metadata is not None
  assert active.label_metadata.variable_labels == (("age", "Age"),)
  assert active.panel_metadata is not None
  assert active.panel_metadata.id_variable == "sex"
  assert active.panel_metadata.time_variable == "age"


def test_cli_gsort_human_and_json(sample_parquet: Path, capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", f"use {sample_parquet}", "-c", "gsort -cost +age"])
  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Sorted by: -cost +age" in captured.out
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {sample_parquet}", "-c", "gsort -cost +age"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]

  assert json_exit_code == 0
  assert envelopes[-1]["result_type"] == "TransformResult"
  assert envelopes[-1]["data"]["message"] == "Sorted by: -cost +age"
  assert json_captured.err == ""


def test_cli_gsort_schema_help_and_no_active(capsys: pytest.CaptureFixture[str]) -> None:
  schema_exit_code = main(["--json", "--describe-command", "gsort"])
  schema_captured = capsys.readouterr()
  schema = json.loads(schema_captured.out)

  assert schema_exit_code == 0
  assert schema["data"] == {
    "arguments": [{"name": "keys", "required": True}],
    "help_topic": "gsort",
    "name": "gsort",
    "options": [],
    "syntax": "gsort [+|-]varlist",
  }

  help_exit_code = main(["-c", "help gsort"])
  help_captured = capsys.readouterr()
  assert help_exit_code == 0
  assert "gsort [+|-]varlist" in help_captured.out

  no_active_exit_code = main(["-c", "gsort -age"])
  no_active_captured = capsys.readouterr()
  assert no_active_exit_code != 0
  assert "active dataset" in no_active_captured.err.lower()

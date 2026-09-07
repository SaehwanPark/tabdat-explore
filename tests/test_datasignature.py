"""Focused coverage for deterministic active-dataset fingerprints."""

import json
from pathlib import Path
from typing import Literal

import duckdb
import pytest

from tabdat.cli import main
from tabdat.errors import ParseError
from tabdat.executor import Executor
from tabdat.models import (
  DatasignatureCommand,
  DatasignatureResult,
  SelectCommand,
  SortCommand,
  UseCommand,
)
from tabdat.parser import parse_command


def _write_complex_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      """
      copy (
        select * from (
          values
            (date '2024-01-01', timestamptz '2024-01-01 12:34:56.123456+00',
             cast('NaN' as double), cast(1.20 as decimal(10, 2)), [1, 2]),
            (null, null, cast('Infinity' as double), null, null)
        ) as signature_data(day, observed_at, score, amount, tags)
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


def test_parse_datasignature_form() -> None:
  assert parse_command("datasignature") == DatasignatureCommand()

  invalid_forms = (
    ("datasignature age", "datasignature does not accept"),
    ("datasignature, fast", "datasignature does not accept"),
    ("datasignature if age > 0", "datasignature does not accept"),
    ("datasignature = value", "assignment requires a target"),
  )
  for text, message in invalid_forms:
    with pytest.raises(ParseError, match=message):
      parse_command(text)


def test_datasignature_is_deterministic_and_preserves_state(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    before = executor.state.active_dataset
    result = executor.execute(DatasignatureCommand())
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert result == DatasignatureResult(
    algorithm="sha256",
    signature="0b61cef05ab04301df893652f666b6ed974668f0cd214ebae17cfff02a6b3aad",
    row_count=3,
    column_count=4,
  )
  assert before == after
  assert executor.state.last_operation == "datasignature"


def test_datasignature_changes_with_row_order_and_schema(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    original = executor.execute(DatasignatureCommand())
    executor.execute(SortCommand(variables=("sex",)))
    reordered = executor.execute(DatasignatureCommand())
    executor.execute(SelectCommand(variables=("age", "bmi", "sex")))
    narrowed = executor.execute(DatasignatureCommand())
  finally:
    executor.close()

  assert isinstance(original, DatasignatureResult)
  assert isinstance(reordered, DatasignatureResult)
  assert isinstance(narrowed, DatasignatureResult)
  assert reordered.signature != original.signature
  assert narrowed.signature != reordered.signature
  assert narrowed.column_count == 3


@pytest.mark.parametrize("lazy_engine", [None, "duckdb", "polars"])
def test_datasignature_preserves_execution_mode(
  sample_parquet: Path,
  lazy_engine: Literal["duckdb", "polars"] | None,
) -> None:
  executor = Executor()
  try:
    if lazy_engine is None:
      executor.execute(UseCommand(sample_parquet))
    else:
      executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=lazy_engine))
    result = executor.execute(DatasignatureCommand())
    active = executor.state.active_dataset
    polars_lazy = executor.backend.is_polars_lazy_active()
  finally:
    executor.close()

  assert isinstance(result, DatasignatureResult)
  assert active is not None
  assert result.signature == "0b61cef05ab04301df893652f666b6ed974668f0cd214ebae17cfff02a6b3aad"
  if lazy_engine is None:
    assert active.execution_mode == "eager"
    assert active.row_count == 3
    assert polars_lazy is False
  else:
    assert active.execution_mode == "lazy"
    assert active.lazy_engine == lazy_engine
    assert active.row_count is None
    assert polars_lazy == (lazy_engine == "polars")


def test_datasignature_canonicalizes_null_nonfinite_temporal_and_decimal_values(
  tmp_path: Path,
) -> None:
  path = tmp_path / "complex.parquet"
  _write_complex_fixture(path)
  signatures: list[str] = []

  for execution_mode, lazy_engine in (
    ("eager", None),
    ("lazy", "duckdb"),
    ("lazy", "polars"),
  ):
    executor = Executor()
    try:
      executor.execute(
        UseCommand(path, execution_mode=execution_mode, lazy_engine=lazy_engine)  # type: ignore[arg-type]
      )
      result = executor.execute(DatasignatureCommand())
    finally:
      executor.close()
    assert isinstance(result, DatasignatureResult)
    assert result.row_count == 2
    signatures.append(result.signature)

  assert len(set(signatures)) == 1


def test_datasignature_empty_dataset_is_valid(tmp_path: Path) -> None:
  path = tmp_path / "empty.parquet"
  _write_empty_fixture(path)
  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    result = executor.execute(DatasignatureCommand())
  finally:
    executor.close()

  assert isinstance(result, DatasignatureResult)
  assert result.row_count == 0
  assert result.column_count == 1
  assert len(result.signature) == 64


def test_cli_datasignature_human_and_json(
  sample_parquet: Path,
  capsys: pytest.CaptureFixture[str],
) -> None:
  exit_code = main(["-c", f"use {sample_parquet}", "-c", "datasignature"])
  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Data signature" in captured.out
  assert "Algorithm: sha256" in captured.out
  assert "Rows: 3" in captured.out
  assert (
    "Signature: 0b61cef05ab04301df893652f666b6ed974668f0cd214ebae17cfff02a6b3aad" in captured.out
  )
  assert captured.err == ""

  json_exit_code = main(["--json", "-c", f"use {sample_parquet}", "-c", "datasignature"])
  json_captured = capsys.readouterr()
  envelopes = [json.loads(line) for line in json_captured.out.splitlines()]

  assert json_exit_code == 0
  assert envelopes[-1] == {
    "data": {
      "algorithm": "sha256",
      "column_count": 4,
      "row_count": 3,
      "signature": "0b61cef05ab04301df893652f666b6ed974668f0cd214ebae17cfff02a6b3aad",
    },
    "result_type": "DatasignatureResult",
    "schema_version": 1,
  }
  assert json_captured.err == ""


def test_cli_datasignature_requires_active_dataset(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", "datasignature"])
  captured = capsys.readouterr()

  assert exit_code != 0
  assert "active dataset" in captured.err.lower()


def test_cli_datasignature_help_schema_and_effects(capsys: pytest.CaptureFixture[str]) -> None:
  schema_exit_code = main(["--json", "--describe-command", "datasignature"])
  schema_captured = capsys.readouterr()
  schema = json.loads(schema_captured.out)

  assert schema_exit_code == 0
  assert schema["data"] == {
    "arguments": [],
    "help_topic": "datasignature",
    "name": "datasignature",
    "options": [],
    "syntax": "datasignature",
  }

  help_exit_code = main(["-c", "help datasignature"])
  help_captured = capsys.readouterr()
  assert help_exit_code == 0
  assert "datasignature" in help_captured.out

  effects_exit_code = main(["--json", "--list-command-effects"])
  effects_captured = capsys.readouterr()
  effects = json.loads(effects_captured.out)
  entry = next(item for item in effects["data"]["commands"] if item["name"] == "datasignature")
  assert effects_exit_code == 0
  assert entry["effects"] == ["read"]

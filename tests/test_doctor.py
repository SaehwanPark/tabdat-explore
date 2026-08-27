"""Tests for the doctor environment and capability diagnostics command."""

import json

import pytest

from tabdat.cli import main
from tabdat.doctor import inspect_environment
from tabdat.errors import ParseError
from tabdat.executor import Executor
from tabdat.formatter import format_result, format_result_json
from tabdat.models import (
  DoctorCapabilityItem,
  DoctorCommand,
  DoctorResult,
)
from tabdat.parser import parse_command


def test_inspect_environment_structure() -> None:
  result = inspect_environment()
  assert isinstance(result, DoctorResult)
  assert result.version is not None
  assert len(result.core) >= 4
  assert len(result.statistics) >= 3
  assert len(result.optional) >= 4
  assert len(result.system) >= 3

  core_names = {item.name for item in result.core}
  assert {"DuckDB", "PyArrow", "Polars", "Plotting"}.issubset(core_names)

  stats_names = {item.name for item in result.statistics}
  assert {"statsmodels", "linearmodels", "scipy"}.issubset(stats_names)

  opt_names = {item.name for item in result.optional}
  assert {"ML", "Bayesian", "Spatial", "R"}.issubset(opt_names)

  sys_names = {item.name for item in result.system}
  assert {"Python", "Platform", "Executable"}.issubset(sys_names)


def test_parser_doctor_valid() -> None:
  cmd = parse_command("doctor")
  assert isinstance(cmd, DoctorCommand)


@pytest.mark.parametrize(
  "invalid_text",
  [
    "doctor foo",
    "doctor, option",
    "doctor if x > 0",
    "doctor = 1",
    "by group: doctor",
  ],
)
def test_parser_doctor_invalid(invalid_text: str) -> None:
  with pytest.raises(ParseError):
    parse_command(invalid_text)


def test_executor_doctor_preserves_state() -> None:
  executor = Executor()
  try:
    res = executor.execute(DoctorCommand())
    assert isinstance(res, DoctorResult)
    assert executor.state.last_operation is None
    assert executor.state.active_dataset is None
  finally:
    executor.close()


def test_formatter_doctor_text() -> None:
  result = DoctorResult(
    version="0.23.0",
    core=(
      DoctorCapabilityItem(name="DuckDB", available=True, version="1.5.2", details="duckdb 1.5.2"),
      DoctorCapabilityItem(name="PyArrow", available=False, version=None, details="missing"),
    ),
    statistics=(
      DoctorCapabilityItem(
        name="statsmodels", available=True, version="0.14.6", details="statsmodels 0.14.6"
      ),
    ),
    optional=(
      DoctorCapabilityItem(name="ML", available=True, version="1.8.0", details="sklearn 1.8.0"),
    ),
    system=(
      DoctorCapabilityItem(name="Python", available=True, version="3.13.0", details="3.13.0"),
    ),
  )
  text = format_result(result)
  assert "TabDat 0.23.0 Environment Diagnostics" in text
  assert "Core Capabilities:" in text
  assert "DuckDB" in text
  assert "✓ duckdb 1.5.2" in text
  assert "PyArrow" in text
  assert "- missing" in text
  assert "Statistics:" in text
  assert "Optional Capabilities:" in text
  assert "System:" in text


def test_formatter_doctor_json() -> None:
  result = inspect_environment()
  json_str = format_result_json(result)
  payload = json.loads(json_str)

  assert payload["schema_version"] == 1
  assert payload["result_type"] == "DoctorResult"
  assert "data" in payload
  assert payload["data"]["version"] == result.version
  assert len(payload["data"]["core"]) == len(result.core)
  assert len(payload["data"]["statistics"]) == len(result.statistics)
  assert len(payload["data"]["optional"]) == len(result.optional)
  assert len(payload["data"]["system"]) == len(result.system)


def test_cli_doctor_positional(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["doctor"])
  assert exit_code == 0
  captured = capsys.readouterr()
  assert "Environment Diagnostics" in captured.out
  assert "Core Capabilities:" in captured.out


def test_cli_doctor_json(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["--json", "doctor"])
  assert exit_code == 0
  captured = capsys.readouterr()
  payload = json.loads(captured.out.strip())
  assert payload["result_type"] == "DoctorResult"
  assert payload["schema_version"] == 1


def test_cli_doctor_batch_command(capsys: pytest.CaptureFixture[str]) -> None:
  exit_code = main(["-c", "doctor"])
  assert exit_code == 0
  captured = capsys.readouterr()
  assert "Environment Diagnostics" in captured.out

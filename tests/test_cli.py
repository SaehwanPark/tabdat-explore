from pathlib import Path

from tabdat.cli import main


def test_cli_runs_phase_1_commands(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "describe",
      "-c",
      "summarize age",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Loaded:" in captured.out
  assert "Rows: 3" in captured.out
  assert "Variable  Type" in captured.out
  assert "Variable  Count  Mean" in captured.out
  assert "age       3      42" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_3_inspection_commands(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "count",
      "-c",
      "codebook sex cost",
      "-c",
      "head 1",
      "-c",
      "tail 1",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Rows: 3" in captured.out
  assert "Variable" in captured.out
  assert "Nonmissing" in captured.out
  assert "Distinct" in captured.out
  assert "sex" in captured.out
  assert "F, M" in captured.out
  assert "cost" in captured.out
  assert "100.0, 150.0" in captured.out
  assert "age  bmi   sex  cost" in captured.out
  assert "30   22.5  F    100.0" in captured.out
  assert "54   27.5  F    ." in captured.out
  assert captured.err == ""


def test_cli_prints_command_errors(capsys) -> None:
  exit_code = main(["-c", "describe"])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert captured.out == ""
  assert "Error: describe requires an active dataset" in captured.err


def test_cli_prints_phase_2_parse_errors(capsys) -> None:
  exit_code = main(["-c", "summarize age if"])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert captured.out == ""
  assert "Error: missing expression after if" in captured.err

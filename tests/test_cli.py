from pathlib import Path

from tabdat.cli import (
  _has_open_sql_triple_quote,
  _open_command_for_platform,
  _open_plot_if_needed,
  main,
)
from tabdat.models import PlotResult


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


def test_cli_runs_full_phase_3_eda_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "keep if age >= 42",
      "-c",
      "generate age2 = age * 2",
      "-c",
      "replace cost = 0 if sex == 'F'",
      "-c",
      "tabulate sex",
      "-c",
      "by sex: summarize age",
      "-c",
      "collapse mean age cost, by(sex)",
      "-c",
      "head 5",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Kept matching rows: 2 rows, 4 columns" in captured.out
  assert "Generated age2: 2 rows, 5 columns" in captured.out
  assert "Replaced cost: 2 rows, 5 columns" in captured.out
  assert "sex  Count  Percent" in captured.out
  assert "F    1      50" in captured.out
  assert "sex  mean_age" in captured.out
  assert "Collapsed dataset: 2 rows, 3 columns" in captured.out
  assert "sex  mean_age  mean_cost" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_4_sql_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "sql select sex, avg(bmi) as mean_bmi from active group by sex order by sex",
      "-c",
      "sql select sex, count(*) as n from active group by sex order by sex into summary",
      "-c",
      "head 5",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "sex  mean_bmi" in captured.out
  assert "F    25" in captured.out
  assert "Created summary: 2 rows, 2 columns" in captured.out
  assert "sex  n" in captured.out
  assert "F    2" in captured.out
  assert "M    1" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_6_plot_flow(sample_parquet: Path, tmp_path: Path, capsys) -> None:
  plot_path = tmp_path / "age.svg"
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      f"histogram age, saving({plot_path})",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert f"Saved plot: {plot_path}" in captured.out
  assert plot_path.read_text().lstrip().startswith("<svg")
  assert captured.err == ""


def test_cli_plot_auto_open_policy(tmp_path: Path) -> None:
  opened: list[Path] = []
  result = PlotResult(path=tmp_path / "plot.svg", should_open=True)

  _open_plot_if_needed(
    result,
    open_plots=False,
    opener=lambda plot: opened.append(plot.path),
  )
  assert opened == []

  _open_plot_if_needed(
    result,
    open_plots=True,
    opener=lambda plot: opened.append(plot.path),
  )
  assert opened == [result.path]

  _open_plot_if_needed(
    PlotResult(path=tmp_path / "closed.svg", should_open=False),
    open_plots=True,
    opener=lambda plot: opened.append(plot.path),
  )
  assert opened == [result.path]


def test_cli_uses_platform_plot_open_commands() -> None:
  assert _open_command_for_platform("darwin") == "open"
  assert _open_command_for_platform("linux") == "xdg-open"
  assert _open_command_for_platform("freebsd") == "xdg-open"


def test_cli_detects_multiline_sql_with_flexible_spacing() -> None:
  assert _has_open_sql_triple_quote('sql """')
  assert _has_open_sql_triple_quote('sql    """')
  assert _has_open_sql_triple_quote('\tsql\t"""')
  assert not _has_open_sql_triple_quote('sql """select * from active"""')
  assert not _has_open_sql_triple_quote('summarize """')


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

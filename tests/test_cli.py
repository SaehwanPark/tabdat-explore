from pathlib import Path

import duckdb
import pytest

from tabdat.cli import (
  _has_open_sql_triple_quote,
  _open_command_for_platform,
  _open_plot_if_needed,
  _run_shell,
  main,
)
from tabdat.executor import Executor
from tabdat.models import PlotResult


def _write_sql_parquet(path: Path, query: str) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(f"copy ({query}) to ? (format parquet)", [str(path)])
  finally:
    connection.close()


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


def test_shell_continues_after_keyboard_interrupt(monkeypatch, capsys) -> None:
  class InterruptThenEofSession:
    def __init__(self) -> None:
      self.calls = 0

    def prompt(self, prompt_text: str) -> str:
      self.calls += 1
      if self.calls == 1:
        raise KeyboardInterrupt
      raise EOFError

  session = InterruptThenEofSession()
  executor = Executor()
  try:
    monkeypatch.setattr("tabdat.cli.create_prompt_session", lambda executor: session)
    exit_code = _run_shell(executor)
  finally:
    executor.close()

  captured = capsys.readouterr()

  assert exit_code == 0
  assert session.calls == 2
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


def test_cli_runs_phase_10_named_table_activation_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "sql select sex, count(*) as n from active group by sex order by sex into summary",
      "-c",
      "keep sex",
      "-c",
      "use summary",
      "-c",
      "head 5",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Created summary: 2 rows, 2 columns" in captured.out
  assert "Kept selected columns: 2 rows, 1 columns" in captured.out
  assert "Activated: summary (2 rows, 1 columns)" in captured.out
  assert "sex" in captured.out
  assert "F" in captured.out
  assert "M" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_11_join_named_table_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "sql select sex, avg(bmi) as mean_bmi from active group by sex into sex_lookup",
      "-c",
      f"use {sample_parquet}",
      "-c",
      "join sex_lookup on sex",
      "-c",
      "head 5",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Created sex_lookup: 2 rows, 2 columns" in captured.out
  assert "Joined sex_lookup: 3 rows, 5 columns" in captured.out
  assert "age  bmi   sex  cost   mean_bmi" in captured.out
  assert "30   22.5  F    100.0  25" in captured.out
  assert "42   25.0  M    150.0  25" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_11_append_named_table_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "sql select age, bmi, sex, cost from active where age > 42 into followup",
      "-c",
      f"use {sample_parquet}",
      "-c",
      "append followup",
      "-c",
      "count",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Created followup: 1 rows, 4 columns" in captured.out
  assert "Appended followup: 4 rows, 4 columns" in captured.out
  assert "Rows: 4" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_11_reshape_long_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "wide.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 10.0, 12.0),
        (2, 20.0, 21.0)
    ) as wide(id, income_2020, income_2021)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "reshape long income, i(id) j(year)",
      "-c",
      "head 4",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Reshaped long: 4 rows, 3 columns" in captured.out
  assert "id  year  income" in captured.out
  assert "1   2020  10" in captured.out
  assert "2   2021  21" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_11_panel_metadata_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0),
        (1, 2021, 12.0),
        (2, 2020, 20.0)
    ) as panel_data(firm_id, year, income)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel",
      "-c",
      "panel firm_id year",
      "-c",
      "panel",
      "-c",
      "panel clear",
      "-c",
      "panel",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Panel: none" in captured.out
  assert "Panel set: id=firm_id, time=year" in captured.out
  assert "Panel: id=firm_id, time=year" in captured.out
  assert "Panel cleared" in captured.out
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


def test_cli_runs_phase_7_lazy_use_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}, lazy engine=polars",
      "-c",
      "select age sex",
      "-c",
      "head 2",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Loaded:" in captured.out
  assert "lazy=polars" in captured.out
  assert "unknown rows" in captured.out
  assert "Selected columns: 3 rows, 2 columns" in captured.out
  assert "age  sex" in captured.out
  assert "30   F" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_8_script_file(sample_parquet: Path, tmp_path: Path, capsys) -> None:
  script_path = tmp_path / "analysis.td"
  plot_path = tmp_path / "age.svg"
  script_path.write_text(
    "\n".join(
      [
        "# mini session",
        f"use {sample_parquet}",
        "keep if age >= 42",
        "sql select sex, count(*) as n from active group by sex order by sex",
        f"histogram age, saving({plot_path})",
      ]
    ),
    encoding="utf-8",
  )

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert f"Script: {script_path}" in captured.out
  assert "TabDat: 0.1.0" in captured.out
  assert "Python:" in captured.out
  assert "Seed: none" in captured.out
  assert "Config: graph_format=svg, artifact_dir=artifacts, graph_open=on" in captured.out
  assert f". use {sample_parquet}" in captured.out
  assert "Kept matching rows: 2 rows, 4 columns" in captured.out
  assert "sex  n" in captured.out
  assert f"Saved plot: {plot_path}" in captured.out
  assert plot_path.read_text().lstrip().startswith("<svg")
  assert captured.err == ""


def test_cli_runs_positional_phase_8_script(sample_parquet: Path, tmp_path: Path, capsys) -> None:
  script_path = tmp_path / "analysis.td"
  script_path.write_text(f"use {sample_parquet}\ncount\n", encoding="utf-8")

  exit_code = main([str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Rows: 3" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_8_script_from_command_mode(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "analysis.td"
  script_path.write_text(f"use {sample_parquet}\ncount\n", encoding="utf-8")

  exit_code = main(["-c", f"run {script_path}"])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert f"Script: {script_path}" in captured.out
  assert ". count" in captured.out
  assert "Rows: 3" in captured.out
  assert captured.err == ""


def test_cli_phase_8_script_reports_line_number(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "bad.td"
  script_path.write_text(f"use {sample_parquet}\nsummarize missing\n", encoding="utf-8")

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert f"Error: {script_path}:2: summarize unknown variable: missing" in captured.err


def test_cli_phase_8_nested_run_resolves_relative_paths(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_dir = tmp_path / "scripts"
  script_dir.mkdir()
  child = script_dir / "child.td"
  parent = script_dir / "parent.td"
  child.write_text("count\n", encoding="utf-8")
  parent.write_text(f"use {sample_parquet}\nrun child.td\n", encoding="utf-8")

  exit_code = main(["-f", str(parent)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert f"Script: {parent}" in captured.out
  assert f"Script: {child}" in captured.out
  assert "Rows: 3" in captured.out
  assert captured.err == ""


def test_cli_phase_8_rejects_recursive_run(tmp_path: Path, capsys) -> None:
  script_path = tmp_path / "loop.td"
  script_path.write_text("run loop.td\n", encoding="utf-8")

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert "recursive script inclusion is not supported" in captured.err


def test_cli_phase_8_script_exit_stops_successfully(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "exit.td"
  script_path.write_text(f"use {sample_parquet}\nexit\nsummarize missing\n", encoding="utf-8")

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert ". exit" in captured.out
  assert "summarize missing" not in captured.out
  assert captured.err == ""


def test_cli_phase_8_rejects_conflicting_script_arguments(
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "analysis.td"
  script_path.write_text("count\n", encoding="utf-8")

  with pytest.raises(SystemExit) as exc_info:
    main(["-c", "count", "-f", str(script_path)])

  captured = capsys.readouterr()

  assert exc_info.value.code == 2
  assert "-c/--command cannot be combined with script execution" in captured.err


def test_cli_phase_11_script_macros_and_seed(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "analysis.td"
  script_path.write_text(
    "\n".join(
      [
        "seed 123",
        f"let data = {sample_parquet}",
        "let adult_filter = age >= 42",
        "use $data",
        "keep if $adult_filter",
        "count",
      ]
    ),
    encoding="utf-8",
  )

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Seed: none" in captured.out
  assert ". seed 123" in captured.out
  assert "Seed: 123" in captured.out
  assert f". let data = {sample_parquet}" in captured.out
  assert "Macro set: data" in captured.out
  assert ". let adult_filter = age >= 42" in captured.out
  assert "Macro set: adult_filter" in captured.out
  assert f". use {sample_parquet}" in captured.out
  assert ". keep if age >= 42" in captured.out
  assert "Rows: 2" in captured.out
  assert captured.err == ""


def test_cli_phase_11_nested_script_shares_macros_and_seed(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_dir = tmp_path / "scripts"
  script_dir.mkdir()
  child = script_dir / "child.td"
  parent = script_dir / "parent.td"
  child.write_text("use $data\ncount\n", encoding="utf-8")
  parent.write_text(f"seed 777\nlet data = {sample_parquet}\nrun child.td\n", encoding="utf-8")

  exit_code = main(["-f", str(parent)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert f"Script: {parent}" in captured.out
  assert f"Script: {child}" in captured.out
  assert "Seed: 777" in captured.out
  assert f". use {sample_parquet}" in captured.out
  assert "Rows: 3" in captured.out
  assert captured.err == ""


def test_cli_phase_11_script_reports_macro_line_number(
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "bad.td"
  script_path.write_text("seed 1\nuse $missing\n", encoding="utf-8")

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert f"Error: {script_path}:2: undefined macro: missing" in captured.err


def test_cli_phase_11_script_conditionals(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "conditionals.td"
  script_path.write_text(
    "\n".join(
      [
        "let mode = duckdb",
        "if $mode == duckdb",
        f"use {sample_parquet}",
        "else",
        "use skipped.parquet",
        "end",
        "if false",
        "count",
        "else",
        "count",
        "end",
      ]
    ),
    encoding="utf-8",
  )

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert ". if duckdb == duckdb" in captured.out
  assert f". use {sample_parquet}" in captured.out
  assert ". use skipped.parquet" not in captured.out
  assert captured.out.count(". count") == 1
  assert "Rows: 3" in captured.out
  assert captured.err == ""


def test_cli_phase_11_script_reports_unterminated_if(
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "bad_if.td"
  script_path.write_text("if false\ncount\n", encoding="utf-8")

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert f"Error: {script_path}:1: if block is missing end" in captured.err


def test_cli_phase_11_inactive_branch_skips_macro_expansion(
  tmp_path: Path,
  capsys,
) -> None:
  script_path = tmp_path / "skip_macro.td"
  script_path.write_text("if false\nuse $missing\nelse\nseed 1\nend\n", encoding="utf-8")

  exit_code = main(["-f", str(script_path)])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert ". use $missing" not in captured.out
  assert "Seed: 1" in captured.out
  assert captured.err == ""


def test_cli_phase_9_loads_explicit_config(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  config_path = tmp_path / "tabdat.toml"
  artifact_dir = tmp_path / "configured"
  config_path.write_text(
    f'graph_format = "png"\nartifact_dir = "{artifact_dir}"\ngraph_open = false\n',
    encoding="utf-8",
  )

  exit_code = main(
    [
      "--config",
      str(config_path),
      "-c",
      f"use {sample_parquet}",
      "-c",
      "histogram age",
    ]
  )

  captured = capsys.readouterr()
  plot_path = artifact_dir / "plots" / "histogram-age.png"

  assert exit_code == 0
  assert f"Saved plot: {plot_path}" in captured.out
  assert plot_path.exists()
  assert captured.err == ""


def test_cli_phase_9_runtime_set_and_save(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  artifact_dir = tmp_path / "plots"
  output_path = tmp_path / "filtered.parquet"

  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "set graph_format png",
      "-c",
      f"set artifact_dir {artifact_dir}",
      "-c",
      "keep if age >= 42",
      "-c",
      "histogram age",
      "-c",
      f"save {output_path}",
    ]
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Set graph_format: png" in captured.out
  assert f"Set artifact_dir: {artifact_dir}" in captured.out
  assert f"Saved plot: {artifact_dir / 'plots' / 'histogram-age.png'}" in captured.out
  assert f"Saved: {output_path} (2 rows, 4 columns)" in captured.out
  assert output_path.exists()
  assert captured.err == ""


def test_cli_phase_9_reports_invalid_config(tmp_path: Path, capsys) -> None:
  config_path = tmp_path / "bad.toml"
  config_path.write_text('graph_format = "pdf"\n', encoding="utf-8")

  exit_code = main(["--config", str(config_path), "-c", "count"])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert "Error: graph_format must be svg or png" in captured.err


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

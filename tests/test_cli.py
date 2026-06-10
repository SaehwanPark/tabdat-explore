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


def _write_spatial_parquet(path: Path) -> None:
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (10.0, 1.0, 1.0, 1.0),
        (12.0, 2.0, 1.5, 2.0),
        (15.0, 3.0, 2.0, 1.5),
        (18.0, 4.0, 2.5, 3.0),
        (20.0, 5.0, 3.0, 2.5),
        (22.0, 6.0, 3.5, 3.5),
        (25.0, 7.0, 4.0, 4.0),
        (28.0, 8.0, 4.5, 4.5)
    ) as sp_data(y, x, lat, lon)
    """,
  )


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


def test_cli_runs_phase_19_spregress_spatial_lag_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "spatial_cli.parquet"
  _write_spatial_parquet(path)
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "spregress y x, coord(lat lon)",
      "-c",
      "predict y_full, spatial_lag",
      "-c",
      "head 2",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Predicted y_full: 8 rows, 5 columns" in captured.out
  assert "y_full" in captured.out
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
  assert "Observations: 3" in captured.out
  assert "Entities: 2" in captured.out
  assert "Time periods: 2" in captured.out
  assert "Obs per entity: min=1, max=2" in captured.out
  assert "Balanced: no" in captured.out
  assert "Panel cleared" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_13_regress_and_predict_flow(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "regress cost age",
      "-c",
      "predict cost_hat",
      "-c",
      "predict cost_resid, residuals",
      "-c",
      "head 3",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: regress cost on age" in captured.out
  assert "Estimator: ols" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Predicted cost_hat: 3 rows, 5 columns" in captured.out
  assert "Predicted cost_resid: 3 rows, 6 columns" in captured.out
  assert "age  bmi   sex  cost   cost_hat  cost_resid" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_lasso_and_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "lasso.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0),
        (2.0, 14.0),
        (3.0, 16.5),
        (4.0, 19.0),
        (5.0, 21.0),
        (6.0, 23.5)
    ) as lasso_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "lasso linear y x, alpha(0.25)",
      "-c",
      "predict yhat",
      "-c",
      "head 3",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: lasso linear y on x" in captured.out
  assert "Estimator: lasso" in captured.out
  assert "Alpha: 0.25" in captured.out
  assert "Predicted yhat: 6 rows, 3 columns" in captured.out
  assert "yhat" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_dml_estat_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "dml.parquet"
  _write_sql_parquet(
    path,
    """
    select
      2.0 * d + x1 as y,
      d,
      x1,
      x2
    from (
      select
        case when x1 + x2 > 1.0 then 1.0 else 0.0 end as d,
        x1,
        x2
      from (
        select
          (row_number() over () % 10) / 10.0 as x1,
          ((row_number() over () * 3) % 10) / 10.0 as x2
        from range(1, 81)
      ) controls
    ) dml_data
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "dml linear y x1 x2, treat(d) folds(3) alpha(0.01) seed(42)",
      "-c",
      "estat dml",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: dml linear y on x1 x2 (treat=d)" in captured.out
  assert "Estimator: dml" in captured.out
  assert "Folds: 3" in captured.out
  assert "Alpha: 0.01" in captured.out
  assert "ATE" in captured.out
  assert "Cross-Fit Folds" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_postlasso_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "postlasso.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (10.0, 1.0, 9.0),
        (12.0, 2.0, 9.0),
        (14.0, 3.0, 9.0),
        (16.0, 4.0, 9.0),
        (18.0, 5.0, 9.0),
        (20.0, 6.0, 9.0)
    ) as postlasso_data(y, x_signal, x_constant)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "postlasso linear y x_signal x_constant, alpha(0.01) robust",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: postlasso linear y on x_signal x_constant" in captured.out
  assert "Estimator: postlasso" in captured.out
  assert "Alpha: 0.01" in captured.out
  assert "Selected Predictors: x_signal" in captured.out
  assert "Covariance: robust" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_ridge_and_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "ridge.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0),
        (2.0, 14.0),
        (3.0, 16.5),
        (4.0, 19.0),
        (5.0, 21.0),
        (6.0, 23.5)
    ) as ridge_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "ridge linear y x, alpha(0.25)",
      "-c",
      "predict yhat",
      "-c",
      "head 3",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: ridge linear y on x" in captured.out
  assert "Estimator: ridge" in captured.out
  assert "Alpha: 0.25" in captured.out
  assert "Predicted yhat: 6 rows, 3 columns" in captured.out
  assert "yhat" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_elasticnet_and_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "elasticnet.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0),
        (2.0, 14.0),
        (3.0, 16.5),
        (4.0, 19.0),
        (5.0, 21.0),
        (6.0, 23.5)
    ) as elasticnet_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "elasticnet linear y x, alpha(0.25) l1_ratio(0.5)",
      "-c",
      "predict yhat",
      "-c",
      "head 3",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: elasticnet linear y on x" in captured.out
  assert "Estimator: elasticnet" in captured.out
  assert "Alpha: 0.25" in captured.out
  assert "L1 Ratio: 0.5" in captured.out
  assert "Predicted yhat: 6 rows, 3 columns" in captured.out
  assert "yhat" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_bayes_and_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "bayes.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0),
        (2.0, 14.0),
        (3.0, 16.5),
        (4.0, 19.0),
        (5.0, 21.0),
        (6.0, 23.5)
    ) as bayes_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "bayes linear y x, n_iter(200) tol(1e-4)",
      "-c",
      "predict yhat",
      "-c",
      "predict resid, residuals",
      "-c",
      "head 3",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: bayes linear y on x" in captured.out
  assert "Estimator: bayesian_ridge" in captured.out
  assert "Noise Precision" in captured.out
  assert "Prior Precision" in captured.out
  assert "Predicted yhat: 6 rows, 3 columns" in captured.out
  assert "Predicted resid: 6 rows, 4 columns" in captured.out
  assert "yhat" in captured.out
  assert "resid" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_19_bayes_prefix_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "bayes_prefix.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0),
        (2.0, 14.0),
        (3.0, 16.5),
        (4.0, 19.0),
        (5.0, 21.0),
        (6.0, 23.5)
    ) as bayes_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "bayes, draws(20) burnin(10) chains(1) seed(42): regress y x",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: bayes: regress y on x" in captured.out
  assert "Estimator: MCMC (bambi)" in captured.out
  assert "Chains: 1" in captured.out
  assert "Draws per chain: 20" in captured.out
  assert "Intercept" in captured.out
  assert "x" in captured.out
  assert "sigma" in captured.out


def test_cli_runs_phase_19_bayes_prefix_posterior_predictive_flow(
  tmp_path: Path,
  capsys,
) -> None:
  path = tmp_path / "bayes_prefix_posterior_predictive.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0),
        (2.0, 14.0),
        (3.0, 16.5),
        (4.0, 19.0),
        (5.0, 21.0),
        (6.0, 23.5)
    ) as bayes_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "bayes, draws(20) burnin(10) chains(1) seed(42): regress y x",
      "-c",
      "predict y_pp, posterior_predictive",
      "-c",
      "head 2",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: bayes: regress y on x" in captured.out
  assert "Predicted y_pp: 6 rows, 3 columns" in captured.out
  assert "y_pp" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_17_qreg_predict_and_estat_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "qreg.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0, 'a'),
        (2.0, 14.0, 'a'),
        (3.0, 16.5, 'b'),
        (4.0, 19.0, 'b'),
        (5.0, 21.0, 'c'),
        (6.0, 23.5, 'c')
    ) as qreg_data(x, y, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "qreg y x, quantile(0.25)",
      "-c",
      "qreg y x, robust",
      "-c",
      "predict qhat",
      "-c",
      "predict qresid, residuals",
      "-c",
      "estat residuals",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: qreg y on x" in captured.out
  assert "Estimator: qreg" in captured.out
  assert "Quantile: 0.25" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Predicted qhat: 6 rows, 4 columns" in captured.out
  assert "Predicted qresid: 6 rows, 5 columns" in captured.out
  assert "studentized_std_dev" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_logit_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "logit.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (0, 22.0, 1.0, 'a'),
        (0, 25.0, 2.0, 'b'),
        (1, 30.0, 2.0, 'b'),
        (1, 34.0, 3.0, 'c'),
        (1, 38.0, 3.0, 'c'),
        (1, 42.0, 4.0, 'd'),
        (1, 45.0, 4.0, 'd')
    ) as logit_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "logit y x z",
      "-c",
      "logit y x z, robust",
      "-c",
      "logit y x z, cluster(cluster_id)",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: logit y on x z" in captured.out
  assert "Estimator: logit" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Pseudo R-squared:" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_probit_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "probit.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (0, 22.0, 1.0, 'a'),
        (0, 25.0, 2.0, 'b'),
        (1, 30.0, 2.0, 'b'),
        (1, 34.0, 3.0, 'c'),
        (1, 38.0, 3.0, 'c'),
        (1, 42.0, 4.0, 'd'),
        (1, 45.0, 4.0, 'd')
    ) as probit_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "probit y x z",
      "-c",
      "probit y x z, robust",
      "-c",
      "probit y x z, cluster(cluster_id)",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: probit y on x z" in captured.out
  assert "Estimator: probit" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Pseudo R-squared:" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_estat_margins_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "binary.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (0, 22.0, 1.0, 'a'),
        (0, 25.0, 2.0, 'b'),
        (1, 30.0, 2.0, 'b'),
        (1, 34.0, 3.0, 'c'),
        (1, 38.0, 3.0, 'c'),
        (1, 42.0, 4.0, 'd'),
        (1, 45.0, 4.0, 'd')
    ) as binary_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "logit y x z",
      "-c",
      "estat margins",
      "-c",
      "probit y x z",
      "-c",
      "estat margins",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: logit y on x z" in captured.out
  assert "Model: probit y on x z" in captured.out
  assert "Variable  Metric" in captured.out
  assert "dy_dx" in captured.out
  assert "ci_lower" in captured.out
  assert "ci_upper" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_binary_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "binary.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (0, 22.0, 1.0, 'a'),
        (0, 25.0, 2.0, 'b'),
        (1, 30.0, 2.0, 'b'),
        (1, 34.0, 3.0, 'c'),
        (1, 38.0, 3.0, 'c'),
        (1, 42.0, 4.0, 'd'),
        (1, 45.0, 4.0, 'd')
    ) as binary_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "logit y x z",
      "-c",
      "predict xb_hat, xb",
      "-c",
      "predict pr_hat, pr",
      "-c",
      "head 2",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Predicted xb_hat: 8 rows, 5 columns" in captured.out
  assert "Predicted pr_hat: 8 rows, 6 columns" in captured.out
  assert "xb_hat" in captured.out
  assert "pr_hat" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_tobit_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "tobit.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 18.0, 1.0, 'a'),
        (0.0, 22.0, 1.0, 'a'),
        (1.5, 25.0, 2.0, 'b'),
        (2.0, 30.0, 2.0, 'b'),
        (4.0, 34.0, 3.0, 'c'),
        (8.0, 38.0, 3.0, 'c'),
        (10.0, 42.0, 4.0, 'd'),
        (10.0, 45.0, 4.0, 'd')
    ) as tobit_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "tobit y x z, ll(0) ul(10)",
      "-c",
      "tobit y x z, ll(0) robust",
      "-c",
      "tobit y x z, ll(0) cluster(cluster_id)",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: tobit y on x z" in captured.out
  assert "Estimator: tobit" in captured.out
  assert "Limits: ll=0, ul=10" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_heckman_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "heckman.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.2, 18.0, 0.2, 0, 'a'),
        (2.1, 22.0, 0.3, 1, 'a'),
        (2.8, 25.0, 0.5, 1, 'b'),
        (3.1, 30.0, 0.7, 1, 'b'),
        (1.0, 34.0, 0.1, 0, 'c'),
        (3.3, 38.0, 0.8, 1, 'c'),
        (0.9, 42.0, 0.2, 0, 'd'),
        (3.5, 45.0, 0.9, 1, 'd')
    ) as heckman_data(y, x, z, s, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "heckman y x, selectdep(s) select(z)",
      "-c",
      "heckman y x, selectdep(s) select(z) robust",
      "-c",
      "heckman y x, selectdep(s) select(z) cluster(cluster_id)",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: heckman y on x (selectdep=s; select=z)" in captured.out
  assert "Estimator: heckman" in captured.out
  assert "Outcome Equation" in captured.out
  assert "Selection Equation" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_15_nl_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "nl.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 2.718281828),
        (2.0, 7.389056099),
        (3.0, 20.08553692),
        (4.0, 54.59815003),
        (5.0, 148.4131591)
    ) as nl_data(x, y)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "nl y = exp(a + b * x), params(a b) start(0.5 0.5)",
      "-c",
      "nl y = exp(a + b * x), params(a b) start(0.5 0.5) robust",
      "-c",
      "predict y_hat, xb",
      "-c",
      "predict u_hat, residuals",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: nl y = exp((a + (b * x)))" in captured.out
  assert "Estimator: nl" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Predicted y_hat: 5 rows, 3 columns" in captured.out
  assert "Predicted u_hat: 5 rows, 4 columns" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_16_poisson_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "poisson.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (1, 22.0, 1.0, 'a'),
        (1, 25.0, 2.0, 'b'),
        (2, 30.0, 2.0, 'b'),
        (3, 34.0, 3.0, 'c'),
        (3, 38.0, 3.0, 'c'),
        (4, 42.0, 4.0, 'd'),
        (5, 45.0, 4.0, 'd')
    ) as poisson_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "poisson y x z",
      "-c",
      "poisson y x z, robust",
      "-c",
      "poisson y x z, cluster(cluster_id)",
      "-c",
      "predict xb_hat, xb",
      "-c",
      "predict u_hat, residuals",
      "-c",
      "estat gof",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: poisson y on x z" in captured.out
  assert "Estimator: poisson" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Predicted xb_hat: 8 rows, 5 columns" in captured.out
  assert "Predicted u_hat: 8 rows, 6 columns" in captured.out
  assert "log_likelihood" in captured.out
  assert "deviance" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_16_nbreg_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "nbreg.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 'a'),
        (1, 22.0, 1.0, 'a'),
        (1, 25.0, 2.0, 'b'),
        (2, 30.0, 2.0, 'b'),
        (3, 34.0, 3.0, 'c'),
        (3, 38.0, 3.0, 'c'),
        (4, 42.0, 4.0, 'd'),
        (5, 45.0, 4.0, 'd')
    ) as nbreg_data(y, x, z, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "nbreg y x z",
      "-c",
      "nbreg y x z, robust",
      "-c",
      "nbreg y x z, cluster(cluster_id)",
      "-c",
      "predict xb_hat, xb",
      "-c",
      "predict u_hat, residuals",
      "-c",
      "estat gof",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: nbreg y on x z" in captured.out
  assert "Estimator: nbreg" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Predicted xb_hat: 8 rows, 5 columns" in captured.out
  assert "Predicted u_hat: 8 rows, 6 columns" in captured.out
  assert "log_likelihood" in captured.out
  assert "pearson_chi2" in captured.out
  assert "lnalpha" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_16_zip_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "zip.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 1.0, 'a'),
        (0, 20.0, 1.0, 2.0, 'a'),
        (1, 25.0, 2.0, 1.0, 'b'),
        (0, 28.0, 2.0, 2.0, 'b'),
        (2, 31.0, 3.0, 1.0, 'c'),
        (0, 35.0, 3.0, 2.0, 'c'),
        (3, 40.0, 4.0, 1.0, 'd'),
        (1, 45.0, 4.0, 2.0, 'd')
    ) as zip_data(y, x, z, zi, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "zip y x z, inflate(zi)",
      "-c",
      "zip y x z, inflate(zi) robust",
      "-c",
      "zip y x z, inflate(zi) cluster(cluster_id)",
      "-c",
      "predict xb_hat, xb",
      "-c",
      "predict u_hat, residuals",
      "-c",
      "estat gof",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: zip y on x z" in captured.out
  assert "Estimator: zip" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Predicted xb_hat: 8 rows, 6 columns" in captured.out
  assert "Predicted u_hat: 8 rows, 7 columns" in captured.out
  assert "log_likelihood" in captured.out
  assert "pearson_chi2" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_16_zinb_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "zinb.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0, 18.0, 1.0, 1.0, 'a'),
        (0, 20.0, 1.0, 2.0, 'a'),
        (1, 25.0, 2.0, 1.0, 'b'),
        (0, 28.0, 2.0, 2.0, 'b'),
        (2, 31.0, 3.0, 1.0, 'c'),
        (0, 35.0, 3.0, 2.0, 'c'),
        (3, 40.0, 4.0, 1.0, 'd'),
        (1, 45.0, 4.0, 2.0, 'd')
    ) as zinb_data(y, x, z, zi, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "zinb y x z, inflate(zi)",
      "-c",
      "zinb y x z, inflate(zi) robust",
      "-c",
      "zinb y x z, inflate(zi) cluster(cluster_id)",
      "-c",
      "predict xb_hat, xb",
      "-c",
      "predict u_hat, residuals",
      "-c",
      "estat gof",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: zinb y on x z" in captured.out
  assert "Estimator: zinb" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Predicted xb_hat: 8 rows, 6 columns" in captured.out
  assert "Predicted u_hat: 8 rows, 7 columns" in captured.out
  assert "log_likelihood" in captured.out
  assert "lnalpha" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_16_streg_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "streg.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 1.0, 30.0, 1.0, 'a'),
        (2.0, 0.0, 35.0, 1.0, 'a'),
        (3.0, 1.0, 40.0, 2.0, 'b'),
        (4.0, 1.0, 28.0, 2.0, 'b'),
        (5.0, 0.0, 50.0, 3.0, 'c'),
        (6.0, 1.0, 45.0, 3.0, 'c'),
        (7.0, 0.0, 33.0, 4.0, 'd'),
        (8.0, 1.0, 38.0, 4.0, 'd')
    ) as streg_data(time, died, age, income, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "streg time age income, failure(died) dist(weibull)",
      "-c",
      "streg time age income, failure(died) dist(exponential) robust",
      "-c",
      "streg time age income, failure(died) dist(weibull) cluster(cluster_id)",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: streg time on age income" in captured.out
  assert "Estimator: streg" in captured.out
  assert "Distribution: weibull" in captured.out
  assert "Distribution: exponential" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_13_weighted_regress_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "weighted.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0, 'a', 1.0, 1.0),
        (2.0, 14.0, 'a', 1.5, 1.5),
        (3.0, 16.5, 'b', 0.5, 0.5),
        (4.0, 19.0, 'b', 2.0, 2.0),
        (5.0, 21.0, 'c', 1.0, 1.0),
        (6.0, 23.5, 'c', 3.0, 3.0)
    ) as reg_data(x, y, cluster_id, weight, sigma)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "regress y x, wls(weight) cluster(cluster_id)",
      "-c",
      "predict y_hat",
      "-c",
      "regress y x, gls(sigma) robust",
      "-c",
      "predict y_resid, residuals",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Estimator: wls" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Predicted y_hat: 6 rows, 6 columns" in captured.out
  assert "Estimator: gls" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Predicted y_resid: 6 rows, 7 columns" in captured.out
  assert captured.err == ""


def test_cli_predict_requires_prior_regress(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "predict cost_hat",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 1
  assert "Loaded:" in captured.out
  assert "Error: predict requires a prior regress" in captured.err


def test_cli_runs_phase_13_estat_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "weighted.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 12.0, 'a', 1.0, 1.0),
        (2.0, 14.0, 'a', 1.5, 1.5),
        (3.0, 16.5, 'b', 0.5, 0.5),
        (4.0, 19.0, 'b', 2.0, 2.0),
        (5.0, 21.0, 'c', 1.0, 1.0),
        (6.0, 23.5, 'c', 3.0, 3.0)
    ) as reg_data(x, y, cluster_id, weight, sigma)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "regress y x, wls(weight)",
      "-c",
      "estat residuals",
      "-c",
      "estat ovtest",
      "-c",
      "estat vif",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Metric" in captured.out
  assert "count" in captured.out
  assert "studentized_std_dev" in captured.out
  assert "df_denom" in captured.out
  assert "Variable  VIF" in captured.out
  assert "x         1" in captured.out
  assert captured.err == ""


def test_cli_estat_requires_prior_regress(sample_parquet: Path, capsys) -> None:
  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "estat ovtest",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 1
  assert "Loaded:" in captured.out
  assert "Error: estat requires a prior regress model" in captured.err


def test_cli_runs_phase_14_ivregress_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "iv.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 10.0, 1.0, 0.0, 'a'),
        (1.0, 12.0, 2.0, 1.0, 'a'),
        (2.0, 15.0, 2.0, 1.0, 'b'),
        (3.0, 16.0, 4.0, 2.0, 'b'),
        (4.0, 18.0, 4.0, 2.0, 'c'),
        (5.0, 20.0, 6.0, 3.0, 'c'),
        (6.0, 21.0, 6.0, 3.0, 'd'),
        (7.0, 24.0, 8.0, 4.0, 'd')
    ) as iv_data(w, y, x_endog, z_inst, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "ivregress 2sls y w, endog(x_endog) iv(z_inst)",
      "-c",
      "ivregress 2sls y w, endog(x_endog) iv(z_inst) robust",
      "-c",
      "ivregress 2sls y w, endog(x_endog) iv(z_inst) cluster(cluster_id)",
      "-c",
      "ivregress gmm y w, endog(x_endog) iv(z_inst)",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: ivregress 2sls y on w (endog=x_endog; iv=z_inst)" in captured.out
  assert "Estimator: 2sls" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Model: ivregress gmm y on w (endog=x_endog; iv=z_inst)" in captured.out
  assert "Estimator: gmm" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_14_cfregress_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "iv.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 10.0, 1.0, 0.0, 'a'),
        (1.0, 12.0, 2.0, 1.0, 'a'),
        (2.0, 15.0, 2.0, 1.0, 'b'),
        (3.0, 16.0, 4.0, 2.0, 'b'),
        (4.0, 18.0, 4.0, 2.0, 'c'),
        (5.0, 20.0, 6.0, 3.0, 'c'),
        (6.0, 21.0, 6.0, 3.0, 'd'),
        (7.0, 24.0, 8.0, 4.0, 'd')
    ) as iv_data(w, y, x_endog, z_inst, cluster_id)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "cfregress y w, endog(x_endog) iv(z_inst)",
      "-c",
      "cfregress y w, endog(x_endog) iv(z_inst) robust",
      "-c",
      "cfregress y w, endog(x_endog) iv(z_inst) cluster(cluster_id)",
      "-c",
      "predict y_hat_cf",
      "-c",
      "predict y_resid_cf, residuals",
      "-c",
      "estat firststage",
      "-c",
      "estat endogenous",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: cfregress y on w (endog=x_endog; iv=z_inst)" in captured.out
  assert "Estimator: control-function" in captured.out
  assert "Covariance: nonrobust" in captured.out
  assert "Covariance: robust" in captured.out
  assert "Covariance: cluster(cluster_id)" in captured.out
  assert "Predicted y_hat_cf: 8 rows, 6 columns" in captured.out
  assert "Predicted y_resid_cf: 8 rows, 7 columns" in captured.out
  assert "first_stage  observation_count" in captured.out
  assert "first_stage  r_squared" in captured.out
  assert "control_function_residual  estimate" in captured.out
  assert "control_function_residual  std_error" in captured.out
  assert "control_function_residual  statistic" in captured.out
  assert "control_function_residual  p_value" in captured.out
  assert "control_function_residual  ci_level" in captured.out
  assert "control_function_residual  ci_lower" in captured.out
  assert "control_function_residual  ci_upper" in captured.out
  assert "control_function_residual  distribution" in captured.out
  assert "control_function_residual  df" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_14_iv_estat_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "iv-overid.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (0.0, 10.0, 1.0, 0.0, 2.0),
        (1.0, 12.0, 2.0, 1.0, 0.0),
        (2.0, 15.0, 2.0, 1.0, 1.0),
        (3.0, 16.0, 4.0, 2.0, 0.0),
        (4.0, 18.0, 4.0, 2.0, 2.0),
        (5.0, 20.0, 6.0, 3.0, 1.0),
        (6.0, 21.0, 6.0, 3.0, 3.0),
        (7.0, 24.0, 8.0, 4.0, 1.0)
    ) as iv_data(w, y, x_endog, z_inst, z_inst2)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "ivregress 2sls y w, endog(x_endog) iv(z_inst z_inst2)",
      "-c",
      "estat firststage",
      "-c",
      "estat overid",
      "-c",
      "estat endogenous",
      "-c",
      "ivregress gmm y w, endog(x_endog) iv(z_inst z_inst2)",
      "-c",
      "estat overid",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Variable  Metric" in captured.out
  assert "partial_f" in captured.out
  assert "Test               Metric" in captured.out
  assert "sargan" in captured.out
  assert "wooldridge_overid" in captured.out
  assert "durbin" in captured.out
  assert "wu_hausman" in captured.out
  assert "gmm_j" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_14_xtreg_and_hausman_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0, 2.0),
        (1, 2021, 11.0, 2.0, 1.0),
        (1, 2022, 13.0, 3.0, 2.0),
        (2, 2020, 14.0, 1.0, 3.0),
        (2, 2021, 15.0, 2.0, 2.0),
        (2, 2022, 16.0, 3.0, 3.0),
        (3, 2020, 9.0, 1.0, 1.0),
        (3, 2021, 10.0, 2.0, 2.0),
        (3, 2022, 11.0, 3.0, 1.0)
    ) as panel_data(firm_id, year, wage, exper, tenure)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "xtreg wage exper tenure, fe robust",
      "-c",
      "xtreg wage exper tenure, re robust",
      "-c",
      "estat hausman",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: xtreg fe wage on exper tenure" in captured.out
  assert "Model: xtreg re wage on exper tenure" in captured.out
  assert "R-squared (within):" in captured.out
  assert "Metric   Value" in captured.out
  assert "chi2" in captured.out
  assert "p_value" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_14_xtdata_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "panel.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0),
        (1, 2021, 11.0, 2.0),
        (1, 2022, 13.0, 3.0),
        (2, 2020, 14.0, 1.0),
        (2, 2021, 15.0, 2.0),
        (2, 2022, 16.0, 3.0)
    ) as panel_data(firm_id, year, wage, exper)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "xtdata wage exper, within",
      "-c",
      "xtdata wage exper, between",
      "-c",
      "head 2",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Applied xtdata within transform: 6 rows, 6 columns" in captured.out
  assert "Applied xtdata between transform: 6 rows, 8 columns" in captured.out
  assert "wage_within" in captured.out
  assert "wage_between" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_17_did_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "did.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.2, 0, 0, 1.1),
        (1, 2021, 11.0, 0, 1, 0.8),
        (2, 2020, 9.8, 0, 0, 1.0),
        (2, 2021, 10.7, 0, 1, 1.2),
        (3, 2020, 10.1, 1, 0, 0.9),
        (3, 2021, 12.8, 1, 1, 1.3),
        (4, 2020, 9.9, 1, 0, 1.0),
        (4, 2021, 12.6, 1, 1, 1.1)
    ) as did_data(firm_id, year, wage, treated, post, exposure)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "did wage exposure, treat(treated) post(post) robust",
      "-c",
      "estat did",
      "-c",
      "predict did_xb",
      "-c",
      "head 2",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: did wage on exposure (treat=treated, post=post)" in captured.out
  assert "Estimator: did_twfe" in captured.out
  assert "Covariance: robust" in captured.out
  assert "did_interaction  coefficient" in captured.out
  assert "Predicted did_xb: 8 rows, 7 columns" in captured.out
  assert "did_xb" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_20_drdid_estat_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "drdid.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.2, 0, 0, 1.1),
        (1, 2021, 11.0, 0, 1, 0.8),
        (2, 2020, 9.8, 0, 0, 1.0),
        (2, 2021, 10.7, 0, 1, 1.2),
        (3, 2020, 10.1, 1, 0, 0.9),
        (3, 2021, 12.8, 1, 1, 1.3),
        (4, 2020, 9.9, 1, 0, 1.0),
        (4, 2021, 12.6, 1, 1, 1.1)
    ) as did_data(firm_id, year, wage, treated, post, exposure)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "drdid wage exposure, treat(treated) post(post) method(aipw)",
      "-c",
      "estat drdid",
    ],
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Model: drdid wage on exposure (treat=treated, post=post)" in captured.out
  assert "Estimator: drdid_aipw" in captured.out
  assert "ATT" in captured.out
  assert "Estimation Method" in captured.out
  assert "AIPW" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_17_xtabond_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "xtabond.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0),
        (1, 2021, 13.0, 2.0),
        (1, 2022, 15.0, 4.0),
        (2, 2020, 7.0, 0.0),
        (2, 2021, 9.0, 1.0),
        (2, 2022, 12.0, 1.5),
        (3, 2020, 20.0, 3.0),
        (3, 2021, 19.0, 2.0),
        (3, 2022, 21.0, 3.0)
    ) as panel_data(firm_id, year, wage, exper)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "xtabond wage exper, robust",
    ],
  )
  captured = capsys.readouterr()
  assert exit_code == 0
  assert "Model: xtabond wage on exper" in captured.out
  assert "Estimator: xtabond_ar1_gmm" in captured.out
  assert "Covariance: robust" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_17_xtabond_overid_and_predict_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "xtabond-overid-predict.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 10.0, 1.0),
        (1, 2021, 13.0, 2.0),
        (1, 2022, 15.0, 4.0),
        (2, 2020, 7.0, 0.0),
        (2, 2021, 9.0, 1.0),
        (2, 2022, 12.0, 1.5),
        (3, 2020, 20.0, 3.0),
        (3, 2021, 19.0, 2.0),
        (3, 2022, 21.0, 3.0)
    ) as panel_data(firm_id, year, wage, exper)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "xtabond wage exper, robust",
      "-c",
      "estat overid",
      "-c",
      "predict xtabond_xb",
      "-c",
      "predict xtabond_resid, residuals",
      "-c",
      "head 8",
    ],
  )

  captured = capsys.readouterr()
  assert exit_code == 0
  assert "Estimator: xtabond_ar1_gmm" in captured.out
  assert "gmm_j  statistic" in captured.out
  assert "Predicted xtabond_xb: 9 rows, 5 columns" in captured.out
  assert "Predicted xtabond_resid: 9 rows, 6 columns" in captured.out
  assert "xtabond_xb" in captured.out
  assert "xtabond_resid" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_17_xtlogit_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "xtlogit.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1, 2020, 0, 0.3, 1.0),
        (1, 2021, 1, 0.8, 1.2),
        (1, 2022, 1, 1.1, 1.4),
        (2, 2020, 0, 0.2, 0.9),
        (2, 2021, 0, 0.4, 1.0),
        (2, 2022, 1, 0.9, 1.3),
        (3, 2020, 0, 0.1, 0.8),
        (3, 2021, 1, 0.9, 1.1),
        (3, 2022, 1, 1.2, 1.5)
    ) as panel_data(firm_id, year, promoted, training, tenure)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "panel firm_id year",
      "-c",
      "xtlogit promoted training tenure, fe robust",
    ],
  )

  captured = capsys.readouterr()
  assert exit_code == 0
  assert "Model: xtlogit promoted on training tenure" in captured.out
  assert "Estimator: xtlogit_fe" in captured.out
  assert "Covariance: robust" in captured.out
  assert captured.err == ""


def test_cli_runs_phase_17_lowess_flow(tmp_path: Path, capsys) -> None:
  path = tmp_path / "lowess.parquet"
  _write_sql_parquet(
    path,
    """
    select * from (
      values
        (1.0, 1.0),
        (2.0, 2.0),
        (3.0, 3.0),
        (4.0, 4.0),
        (5.0, 5.0)
    ) as lowess_data(wage, exper)
    """,
  )
  exit_code = main(
    [
      "-c",
      f"use {path}",
      "-c",
      "lowess wage exper, gen(wage_lowess) bandwidth=0.5",
      "-c",
      "head 5",
    ],
  )

  captured = capsys.readouterr()
  assert exit_code == 0
  assert "Generated wage_lowess with lowess: 5 rows, 3 columns" in captured.out
  assert "wage_lowess" in captured.out
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
  assert "Selected columns: unknown rows, 2 columns" in captured.out
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


def test_cli_phase_9_uses_xdg_default_config_when_project_config_is_missing(
  sample_parquet: Path,
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()
  xdg_home = tmp_path / "xdg"
  artifact_dir = tmp_path / "configured"
  config_path = xdg_home / "tabdat" / "config.toml"
  config_path.parent.mkdir(parents=True)
  config_path.write_text(
    f'graph_format = "png"\nartifact_dir = "{artifact_dir}"\ngraph_open = false\n',
    encoding="utf-8",
  )
  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

  exit_code = main(
    [
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


def test_cli_phase_9_prefers_project_config_over_xdg_default(
  sample_parquet: Path,
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()
  project_artifact_dir = tmp_path / "project-artifacts"
  project_config = project_dir / ".tabdat.toml"
  project_config.write_text(
    f'graph_format = "png"\nartifact_dir = "{project_artifact_dir}"\ngraph_open = false\n',
    encoding="utf-8",
  )
  xdg_home = tmp_path / "xdg"
  xdg_config = xdg_home / "tabdat" / "config.toml"
  xdg_config.parent.mkdir(parents=True)
  xdg_config.write_text('graph_format = "svg"\n', encoding="utf-8")
  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

  exit_code = main(
    [
      "-c",
      f"use {sample_parquet}",
      "-c",
      "histogram age",
    ]
  )

  captured = capsys.readouterr()
  plot_path = project_artifact_dir / "plots" / "histogram-age.png"

  assert exit_code == 0
  assert f"Saved plot: {plot_path}" in captured.out
  assert plot_path.exists()
  assert captured.err == ""


def test_cli_phase_9_reports_invalid_xdg_config(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()
  xdg_home = tmp_path / "xdg"
  xdg_config = xdg_home / "tabdat" / "config.toml"
  xdg_config.parent.mkdir(parents=True)
  xdg_config.write_text('graph_format = "pdf"\n', encoding="utf-8")
  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

  exit_code = main(["-c", "count"])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert "Error: graph_format must be svg or png" in captured.err


def test_cli_phase_9_runtime_set_and_save(
  sample_parquet: Path,
  tmp_path: Path,
  capsys,
) -> None:
  artifact_dir = tmp_path / "plots"
  output_path = tmp_path / "filtered.parquet"
  export_path = tmp_path / "filtered.csv"

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
      "-c",
      f"export {export_path}",
    ]
  )

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "Set graph_format: png" in captured.out
  assert f"Set artifact_dir: {artifact_dir}" in captured.out
  assert f"Saved plot: {artifact_dir / 'plots' / 'histogram-age.png'}" in captured.out
  assert f"Saved: {output_path} (2 rows, 4 columns)" in captured.out
  assert f"Exported: {export_path} (2 rows, 4 columns)" in captured.out
  assert output_path.exists()
  assert export_path.exists()
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


def test_shell_default_plot_paths_avoid_overwriting_existing_artifacts(
  sample_parquet: Path,
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys,
) -> None:
  class FixedPromptSession:
    def __init__(self) -> None:
      self.commands = iter(
        (
          f"use {sample_parquet}",
          "histogram age",
          "histogram age",
        )
      )

    def prompt(self, prompt_text: str) -> str:
      try:
        return next(self.commands)
      except StopIteration as exc:
        raise EOFError from exc

  project_dir = tmp_path / "project"
  project_dir.mkdir()
  monkeypatch.chdir(project_dir)
  monkeypatch.setattr("tabdat.cli.create_prompt_session", lambda executor: FixedPromptSession())

  exit_code = main([])

  captured = capsys.readouterr()
  first_plot = project_dir / "artifacts" / "plots" / "histogram-age.svg"
  second_plot = project_dir / "artifacts" / "plots" / "histogram-age-2.svg"

  assert exit_code == 0
  assert "Saved plot: artifacts/plots/histogram-age.svg" in captured.out
  assert "Saved plot: artifacts/plots/histogram-age-2.svg" in captured.out
  assert first_plot.exists()
  assert second_plot.exists()
  assert captured.err == ""


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


@pytest.mark.parametrize("command_text", ["help summarize", "? summarize"])
def test_cli_prints_in_app_help_for_explicit_topic(command_text: str, capsys) -> None:
  exit_code = main(["-c", command_text])

  captured = capsys.readouterr()

  assert exit_code == 0
  assert "How to invoke" in captured.out
  assert "Examples" in captured.out
  assert captured.err == ""


def test_cli_rejects_bare_help_outside_interactive_shell(capsys) -> None:
  exit_code = main(["-c", "help"])

  captured = capsys.readouterr()

  assert exit_code == 1
  assert captured.out == ""
  assert "help requires a command name outside the interactive shell" in captured.err


def test_cli_shell_prompts_for_help_topic_then_prints_help(monkeypatch, capsys) -> None:
  class HelpSession:
    def __init__(self) -> None:
      self.calls = 0

    def prompt(self, prompt_text: str) -> str:
      self.calls += 1
      if self.calls == 1:
        return "help"
      if self.calls == 2:
        return "1"
      raise EOFError

  session = HelpSession()
  executor = Executor()
  try:
    monkeypatch.setattr("tabdat.cli.create_prompt_session", lambda executor: session)
    exit_code = _run_shell(executor)
  finally:
    executor.close()

  captured = capsys.readouterr()

  assert exit_code == 0
  assert session.calls == 3
  assert "Available help topics:" in captured.out
  assert "How to invoke" in captured.out
  assert captured.err == ""


def test_cli_shell_cancels_bare_help_without_printing_topic(monkeypatch, capsys) -> None:
  class CancelHelpSession:
    def __init__(self) -> None:
      self.calls = 0

    def prompt(self, prompt_text: str) -> str:
      self.calls += 1
      if self.calls == 1:
        return "help"
      if self.calls == 2:
        return ""
      raise EOFError

  session = CancelHelpSession()
  executor = Executor()
  try:
    monkeypatch.setattr("tabdat.cli.create_prompt_session", lambda executor: session)
    exit_code = _run_shell(executor)
  finally:
    executor.close()

  captured = capsys.readouterr()

  assert exit_code == 0
  assert session.calls == 3
  assert "Available help topics:" in captured.out
  assert "How to invoke" not in captured.out
  assert captured.err == ""

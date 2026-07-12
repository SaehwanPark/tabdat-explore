from pathlib import Path

import duckdb

from tabdat.cli import main


def _write_canonical_fixture(path: Path) -> None:
  connection = duckdb.connect(database=":memory:")
  try:
    connection.execute(
      """
      copy (
        select * from (
          values
            (17, 20.0, 1, 0, 'first', 'S', 1),
            (25, 100.0, 1, 0, 'first', 'S', 1),
            (30, null, 2, 1, 'second', 'C', 0),
            (40, 40.0, 0, 0, 'second', null, 1),
            (50, 60.0, 3, 2, 'third', 'S', 0),
            (60, 80.0, null, 1, 'third', 'Q', 0)
        ) as canonical(age, fare, sibsp, parch, class, embarked, survived)
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()


def _parquet_snapshot(path: Path) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
  connection = duckdb.connect(database=":memory:")
  try:
    cursor = connection.execute("select * from read_parquet(?) order by all", [str(path)])
    columns = tuple(column[0] for column in cursor.description or ())
    rows = tuple(cursor.fetchall())
    return columns, rows
  finally:
    connection.close()


def test_canonical_parquet_workflow_replays_deterministically(tmp_path: Path, capsys) -> None:
  source = tmp_path / "source.parquet"
  output = tmp_path / "canonical_summary.parquet"
  _write_canonical_fixture(source)

  script = Path("demos/canonical_parquet_eda.td").read_text(encoding="utf-8")
  script = script.replace("artifacts/e2e/data/titanic.parquet", str(source))
  script = script.replace("artifacts/e2e/s6/canonical_summary.parquet", str(output))
  script_path = tmp_path / "canonical.td"
  script_path.write_text(script, encoding="utf-8")

  first_exit = main(["-f", str(script_path)])
  first = capsys.readouterr()
  first_snapshot = _parquet_snapshot(output)

  second_exit = main(["-f", str(script_path)])
  second = capsys.readouterr()
  second_snapshot = _parquet_snapshot(output)

  assert first_exit == second_exit == 0
  assert first.err == second.err == ""
  assert first.out == second.out
  assert "lazy=duckdb" in first.out
  assert "Missing" in first.out
  assert "by class: summarize fare" in first.out
  assert "Exported:" in first.out
  assert first_snapshot == second_snapshot
  assert first_snapshot[0] == ("class", "mean_age", "mean_fare", "mean_family_size")
  assert len(first_snapshot[1]) == 3

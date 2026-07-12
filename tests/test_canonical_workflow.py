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
            (17, 20.0, 1, 0, 'first'),
            (25, 100.0, 1, 0, 'first'),
            (30, null, 2, 1, 'second'),
            (40, 40.0, 0, 0, 'second'),
            (50, 60.0, 3, 2, 'third'),
            (60, 80.0, null, 1, 'third')
        ) as canonical(age, fare, sibsp, parch, class)
      ) to ? (format parquet)
      """,
      [str(path)],
    )
  finally:
    connection.close()


def _parquet_snapshot(
  path: Path,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[object, ...], ...]]:
  connection = duckdb.connect(database=":memory:")
  try:
    cursor = connection.execute("select * from read_parquet(?) order by all", [str(path)])
    columns = tuple((column[0], str(column[1])) for column in cursor.description or ())
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
  assert first_snapshot[0] == (
    ("class", "VARCHAR"),
    ("mean_age", "DOUBLE"),
    ("mean_fare", "DOUBLE"),
    ("mean_family_size", "DOUBLE"),
  )
  assert first_snapshot[1] == (
    ("first", 25.0, 100.0, 2.0),
    ("second", 35.0, 40.0, 2.5),
    ("third", 55.0, 70.0, 6.0),
  )

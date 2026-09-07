"""Coverage for tabulate value-label display."""

from pathlib import Path

from tabdat.executor import Executor
from tabdat.models import (
  LabelCommand,
  TableResult,
  TabulateCommand,
  UseCommand,
)
from tabdat.parser import parse_command


def test_parse_tabulate_nolabel() -> None:
  assert parse_command("tabulate sex, nolabel") == TabulateCommand(
    row_variables=("sex",),
    nolabel=True,
  )
  assert parse_command("tabulate sex age, row col missing nolabel") == TabulateCommand(
    row_variables=("sex",),
    column_variables=("age",),
    row_percent=True,
    column_percent=True,
    include_missing=True,
    nolabel=True,
  )


def test_tabulate_uses_attached_value_labels(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      LabelCommand(action="define", set_name="sexlbl", mappings=(("F", "Female"), ("M", "Male")))
    )
    executor.execute(LabelCommand(action="values", variable="sex", set_name="sexlbl"))
    labeled = executor.execute(TabulateCommand(row_variables=("sex",)))
    raw = executor.execute(TabulateCommand(row_variables=("sex",), nolabel=True))
  finally:
    executor.close()

  assert isinstance(labeled, TableResult)
  assert isinstance(raw, TableResult)
  labeled_categories = {row[0] for row in labeled.rows}
  raw_categories = {row[0] for row in raw.rows}
  assert labeled_categories == {"Female", "Male"}
  assert raw_categories == {"F", "M"}


def test_tabulate_two_way_headers_use_value_labels(tmp_path: Path) -> None:
  path = tmp_path / "codes.parquet"
  import duckdb

  duckdb.connect().execute(
    """
    copy (
      select * from (values (0, 1), (0, 0), (1, 1), (1, 1)) as t(group_id, code)
    ) to ? (format parquet)
    """,
    [str(path)],
  ).close()

  executor = Executor()
  try:
    executor.execute(UseCommand(path))
    executor.execute(
      LabelCommand(
        action="define",
        set_name="codelbl",
        mappings=((0, "No"), (1, "Yes")),
      )
    )
    executor.execute(LabelCommand(action="values", variable="code", set_name="codelbl"))
    result = executor.execute(
      TabulateCommand(row_variables=("group_id",), column_variables=("code",))
    )
  finally:
    executor.close()

  assert isinstance(result, TableResult)
  assert any(header.startswith("No ") for header in result.headers)
  assert any(header.startswith("Yes ") for header in result.headers)
  assert not any(header.startswith("0 ") for header in result.headers)
  assert not any(header.startswith("1 ") for header in result.headers)

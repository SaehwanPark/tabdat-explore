import pytest
from pydantic import ValidationError

from tabdat.models import (
  ColumnInfo,
  CommandOption,
  DatasetInfo,
  HeadCommand,
  KeepCommand,
  UseCommand,
)


@pytest.mark.parametrize(
  ("factory", "kwargs"),
  [
    (HeadCommand, {"limit": "5"}),
    (UseCommand, {"path": 123}),
    (KeepCommand, {"variables": ["age"]}),
    (CommandOption, {"name": 1}),
  ],
)
def test_models_reject_invalid_runtime_types(factory: type, kwargs: dict[str, object]) -> None:
  with pytest.raises(ValidationError):
    factory(**kwargs)


def test_use_command_accepts_remote_uri_string() -> None:
  assert UseCommand("https://example.com/data.parquet").path == "https://example.com/data.parquet"


def test_dataset_info_preserves_remote_uri_string() -> None:
  dataset = DatasetInfo(
    path="https://example.com/data.parquet",
    row_count=None,
    columns=(ColumnInfo("age", "INTEGER"),),
    execution_mode="lazy",
    lazy_engine="duckdb",
  )

  assert dataset.path == "https://example.com/data.parquet"

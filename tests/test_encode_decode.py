"""Focused coverage for encode and decode."""

from pathlib import Path

import pytest

from tabdat.errors import ExecutionError, ParseError, TypeMismatchExecutionError
from tabdat.executor import Executor
from tabdat.models import (
  DecodeCommand,
  EncodeCommand,
  LabelCommand,
  TabulateCommand,
  UseCommand,
)
from tabdat.parser import parse_command


def test_parse_encode_decode() -> None:
  assert parse_command("encode sex, generate(sex_n)") == EncodeCommand(
    source="sex",
    generate="sex_n",
  )
  assert parse_command("encode region, generate(rid) label(regionlbl)") == EncodeCommand(
    source="region",
    generate="rid",
    label="regionlbl",
  )
  assert parse_command("decode sex_n, generate(sex_str)") == DecodeCommand(
    source="sex_n",
    generate="sex_str",
  )


def test_parse_encode_decode_rejects_invalid() -> None:
  with pytest.raises(ParseError, match="generate"):
    parse_command("encode sex")
  with pytest.raises(ParseError, match="generate"):
    parse_command("decode sex_n")


def test_encode_decode_roundtrip_with_tabulate_labels(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    encoded = executor.execute(EncodeCommand(source="sex", generate="sex_n"))
    labeled_tab = executor.execute(TabulateCommand(row_variables=("sex_n",)))
    decoded = executor.execute(DecodeCommand(source="sex_n", generate="sex_str"))
    raw_tab = executor.execute(TabulateCommand(row_variables=("sex_n",), nolabel=True))
    dataset = executor.state.active_dataset
  finally:
    executor.close()

  assert "Encoded sex -> sex_n" in encoded.message
  assert "Decoded sex_n -> sex_str" in decoded.message
  categories = {row[0] for row in labeled_tab.rows}
  assert categories == {"F", "M"}
  codes = {row[0] for row in raw_tab.rows}
  assert codes == {1, 2}
  assert dataset is not None
  assert dataset.label_metadata is not None
  assert ("sex_n", "sex_n") in dataset.label_metadata.attachments


def test_encode_requires_string(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(TypeMismatchExecutionError, match="string"):
      executor.execute(EncodeCommand(source="age", generate="age_n"))
  finally:
    executor.close()


def test_decode_requires_attached_labels(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="attached value labels"):
      executor.execute(DecodeCommand(source="age", generate="age_str"))
  finally:
    executor.close()


def test_encode_copies_variable_label(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="variable", variable="sex", text="Sex"))
    executor.execute(EncodeCommand(source="sex", generate="sex_n"))
    dataset = executor.state.active_dataset
  finally:
    executor.close()
  assert dataset is not None and dataset.label_metadata is not None
  assert dict(dataset.label_metadata.variable_labels)["sex_n"] == "Sex"

"""Focused coverage for session-local variable and value labels."""

from pathlib import Path

import pytest

from tabdat.errors import ExecutionError, ParseError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.formatter import format_result
from tabdat.models import (
  CodebookCommand,
  CodebookResult,
  DescribeCommand,
  DescribeResult,
  DropCommand,
  LabelCommand,
  LabelMetadata,
  LabelResult,
  RenameCommand,
  UseCommand,
  ValueLabelSet,
)
from tabdat.parser import parse_command


def test_parse_label_commands() -> None:
  assert parse_command('label variable age "Age in years"') == LabelCommand(
    action="variable",
    variable="age",
    text="Age in years",
  )
  assert parse_command("label variable age, clear") == LabelCommand(
    action="variable",
    variable="age",
    clear=True,
  )
  assert parse_command('label define sexlbl 0 "Male" 1 "Female"') == LabelCommand(
    action="define",
    set_name="sexlbl",
    mappings=((0, "Male"), (1, "Female")),
  )
  assert parse_command('label define sexlbl -1 "Missing", replace') == LabelCommand(
    action="define",
    set_name="sexlbl",
    mappings=((-1, "Missing"),),
    replace=True,
  )
  assert parse_command("label values sex sexlbl") == LabelCommand(
    action="values",
    variable="sex",
    set_name="sexlbl",
  )
  assert parse_command("label values sex, clear") == LabelCommand(
    action="values",
    variable="sex",
    clear=True,
  )
  assert parse_command("label list") == LabelCommand(action="list")
  assert parse_command("label list sexlbl other") == LabelCommand(
    action="list",
    names=("sexlbl", "other"),
  )
  assert parse_command("label drop sexlbl") == LabelCommand(action="drop", names=("sexlbl",))


def test_parse_label_rejects_invalid_forms() -> None:
  with pytest.raises(ParseError, match="label variable expects syntax"):
    parse_command("label variable age Age")
  with pytest.raises(ParseError, match="quoted string"):
    parse_command("label define sexlbl 0 Male")
  with pytest.raises(ParseError, match="at least one label set name"):
    parse_command("label drop")
  with pytest.raises(ParseError, match="variable\\|define\\|values\\|list\\|drop"):
    parse_command("label note age")


def test_label_variable_define_values_list_and_describe(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    labeled = executor.execute(LabelCommand(action="variable", variable="age", text="Age years"))
    defined = executor.execute(
      LabelCommand(
        action="define",
        set_name="sexlbl",
        mappings=((0, "Male"), (1, "Female")),
      )
    )
    attached = executor.execute(LabelCommand(action="values", variable="sex", set_name="sexlbl"))
    listed = executor.execute(LabelCommand(action="list"))
    described = executor.execute(DescribeCommand())
    codebook = executor.execute(CodebookCommand(("age", "sex")))
  finally:
    executor.close()

  assert isinstance(labeled, LabelResult)
  assert labeled.message == "Labeled variable age"
  assert isinstance(defined, LabelResult)
  assert isinstance(attached, LabelResult)
  assert isinstance(listed, LabelResult)
  assert listed.metadata == LabelMetadata(
    variable_labels=(("age", "Age years"),),
    value_sets=(ValueLabelSet("sexlbl", ((0, "Male"), (1, "Female"))),),
    attachments=(("sex", "sexlbl"),),
  )
  assert isinstance(described, DescribeResult)
  assert described.dataset.label_metadata == listed.metadata
  text = format_result(described)
  assert "Label" in text
  assert "Age years" in text
  assert isinstance(codebook, CodebookResult)
  assert codebook.rows[0].variable_label == "Age years"
  assert codebook.rows[1].variable_label is None
  assert "Label" in format_result(codebook)


def test_label_rename_and_drop_preserve_or_prune(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="variable", variable="age", text="Age"))
    executor.execute(LabelCommand(action="define", set_name="sexlbl", mappings=((0, "Male"),)))
    executor.execute(LabelCommand(action="values", variable="sex", set_name="sexlbl"))
    executor.execute(RenameCommand("age", "years"))
    after_rename = executor.execute(LabelCommand(action="list"))
    executor.execute(DropCommand(variables=("sex",)))
    after_drop = executor.execute(LabelCommand(action="list"))
    dropped = executor.execute(LabelCommand(action="drop", names=("sexlbl",)))
  finally:
    executor.close()

  assert after_rename.metadata is not None
  assert after_rename.metadata.variable_labels == (("years", "Age"),)
  assert after_rename.metadata.attachments == (("sex", "sexlbl"),)
  assert after_drop.metadata is not None
  assert after_drop.metadata.attachments == ()
  assert after_drop.metadata.value_sets == (ValueLabelSet("sexlbl", ((0, "Male"),)),)
  assert isinstance(dropped, LabelResult)
  assert dropped.metadata == LabelMetadata(
    variable_labels=(("years", "Age"),),
    value_sets=(),
    attachments=(),
  )


def test_label_define_without_replace_is_atomic(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="define", set_name="sexlbl", mappings=((0, "Male"),)))
    before = executor.state.active_dataset
    with pytest.raises(ExecutionError, match="already exists"):
      executor.execute(LabelCommand(action="define", set_name="sexlbl", mappings=((1, "Female"),)))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before is not None and after is not None
  assert before.label_metadata == after.label_metadata


def test_label_unknown_variable(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="missing"):
      executor.execute(LabelCommand(action="variable", variable="missing", text="x"))
  finally:
    executor.close()

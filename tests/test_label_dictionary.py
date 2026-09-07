"""Focused coverage for reusable label-dictionary JSON files."""

from pathlib import Path

import pytest

from tabdat.errors import ExecutionError, UnknownVariableError
from tabdat.executor import Executor
from tabdat.labels import (
  LabelDictionaryError,
  deserialize_label_metadata,
  load_label_metadata,
  save_label_metadata,
  serialize_label_metadata,
)
from tabdat.models import (
  LabelCommand,
  LabelMetadata,
  LabelResult,
  UseCommand,
  ValueLabelSet,
)


def _metadata() -> LabelMetadata:
  return LabelMetadata(
    variable_labels=(("age", "Age in years"),),
    value_sets=(ValueLabelSet("sexlbl", ((0, "Male"), (1, "Female"))),),
    attachments=(("sex", "sexlbl"),),
  )


def test_label_dictionary_json_is_versioned_and_deterministic() -> None:
  metadata = _metadata()

  serialized = serialize_label_metadata(metadata)

  assert serialized == (
    "{\n"
    '  "metadata": {\n'
    '    "attachments": [\n'
    "      [\n"
    '        "sex",\n'
    '        "sexlbl"\n'
    "      ]\n"
    "    ],\n"
    '    "value_sets": [\n'
    "      {\n"
    '        "mappings": [\n'
    "          [\n"
    "            0,\n"
    '            "Male"\n'
    "          ],\n"
    "          [\n"
    "            1,\n"
    '            "Female"\n'
    "          ]\n"
    "        ],\n"
    '        "name": "sexlbl"\n'
    "      }\n"
    "    ],\n"
    '    "variable_labels": [\n'
    "      [\n"
    '        "age",\n'
    '        "Age in years"\n'
    "      ]\n"
    "    ]\n"
    "  },\n"
    '  "schema_version": 1\n'
    "}\n"
  )
  assert deserialize_label_metadata(serialized) == metadata


def test_label_dictionary_rejects_unsupported_or_ambiguous_documents() -> None:
  with pytest.raises(LabelDictionaryError, match="invalid label dictionary JSON"):
    deserialize_label_metadata('{"schema_version": 1,')
  with pytest.raises(LabelDictionaryError, match="schema version"):
    deserialize_label_metadata('{"schema_version": 2, "metadata": {}}')
  with pytest.raises(LabelDictionaryError, match="unsupported fields"):
    deserialize_label_metadata('{"schema_version": 1, "metadata": {}, "extra": 1}')
  with pytest.raises(LabelDictionaryError, match="unsupported fields"):
    deserialize_label_metadata(
      '{"schema_version": 1, "metadata": '
      '{"attachments": [], "value_sets": [], "variable_labels": [], "extra": 1}}'
    )
  with pytest.raises(LabelDictionaryError, match="metadata must be a JSON object"):
    deserialize_label_metadata('{"schema_version": 1, "metadata": []}')
  with pytest.raises(LabelDictionaryError, match="duplicate values"):
    deserialize_label_metadata(
      '{"schema_version": 1, "metadata": {'
      '"attachments": [], "value_sets": [{"name": "x", '
      '"mappings": [[0, "zero"], [0, "again"]]}], "variable_labels": []}}'
    )
  with pytest.raises(LabelDictionaryError, match="duplicate values"):
    deserialize_label_metadata(
      '{"schema_version": 1, "metadata": {'
      '"attachments": [], "value_sets": [{"name": "x", '
      '"mappings": [[1, "one"], [1.0, "also one"]]}], "variable_labels": []}}'
    )


def test_label_dictionary_file_roundtrip_and_replace(tmp_path: Path) -> None:
  path = tmp_path / "labels.json"

  save_label_metadata(path, _metadata(), replace=False)
  assert load_label_metadata(path) == _metadata()
  with pytest.raises(FileExistsError):
    save_label_metadata(path, LabelMetadata(), replace=False)
  save_label_metadata(path, LabelMetadata(), replace=True)
  assert load_label_metadata(path) == LabelMetadata()


def test_label_save_and_use_roundtrip_is_atomic(sample_parquet: Path, tmp_path: Path) -> None:
  path = tmp_path / "labels.json"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="variable", variable="age", text="Age"))
    executor.execute(
      LabelCommand(
        action="define",
        set_name="sexlbl",
        mappings=((0, "Male"), (1, "Female")),
      )
    )
    executor.execute(LabelCommand(action="values", variable="sex", set_name="sexlbl"))
    saved = executor.execute(LabelCommand(action="save", path=path))
    before = executor.state.active_dataset
    with pytest.raises(ExecutionError, match="target already exists"):
      executor.execute(LabelCommand(action="save", path=path))
    loaded = executor.execute(LabelCommand(action="use", path=path))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(saved, LabelResult)
  assert saved.message == f"Saved label dictionary: {path}"
  assert isinstance(loaded, LabelResult)
  assert loaded.message == f"Loaded label dictionary: {path}"
  assert before is not None and after is not None
  assert after.label_metadata == LabelMetadata(
    variable_labels=(("age", "Age"),),
    value_sets=(ValueLabelSet("sexlbl", ((0, "Male"), (1, "Female"))),),
    attachments=(("sex", "sexlbl"),),
  )


def test_label_use_rejects_unknown_variable_without_replacing_metadata(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  path = tmp_path / "invalid-labels.json"
  path.write_text(
    serialize_label_metadata(LabelMetadata(variable_labels=(("missing", "Not here"),))),
    encoding="utf-8",
  )
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(LabelCommand(action="variable", variable="age", text="Age"))
    before = executor.state.active_dataset
    with pytest.raises(UnknownVariableError, match="missing"):
      executor.execute(LabelCommand(action="use", path=path))
    after = executor.state.active_dataset
  finally:
    executor.close()

  assert before is not None and after is not None
  assert before.label_metadata == after.label_metadata


def test_label_metadata_operations_do_not_materialize_polars_lazy(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  path = tmp_path / "labels.json"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine="polars"))
    saved = executor.execute(LabelCommand(action="save", path=path))
    loaded = executor.execute(LabelCommand(action="use", path=path))
    active = executor.state.active_dataset
  finally:
    executor.close()

  assert isinstance(saved, LabelResult)
  assert isinstance(loaded, LabelResult)
  assert active is not None
  assert active.execution_mode == "lazy"
  assert active.lazy_engine == "polars"
  assert active.row_count is None

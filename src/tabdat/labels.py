"""Pure serialization helpers for TabDat data-dictionary metadata."""

import json
import math
import os
import tempfile
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from tabdat.models import LabelMetadata

LABEL_DICTIONARY_SCHEMA_VERSION = 1
_LABEL_DICTIONARY_KEYS = frozenset({"metadata", "schema_version"})
_LABEL_METADATA_KEYS = frozenset({"attachments", "value_sets", "variable_labels"})
_LABEL_METADATA_ADAPTER = TypeAdapter(LabelMetadata)


class LabelDictionaryError(ValueError):
  """Raised when a label dictionary is not a supported TabDat document."""


def serialize_label_metadata(metadata: LabelMetadata) -> str:
  """Return deterministic, versioned JSON for one label dictionary."""
  validate_label_metadata(metadata)
  payload = {
    "schema_version": LABEL_DICTIONARY_SCHEMA_VERSION,
    "metadata": _LABEL_METADATA_ADAPTER.dump_python(metadata, mode="json"),
  }
  return (
    json.dumps(
      payload,
      ensure_ascii=False,
      allow_nan=False,
      indent=2,
      sort_keys=True,
    )
    + "\n"
  )


def deserialize_label_metadata(text: str) -> LabelMetadata:
  """Parse and validate one versioned label dictionary JSON document."""
  try:
    document = json.loads(text, parse_constant=_reject_json_constant)
  except (TypeError, ValueError, json.JSONDecodeError) as exc:
    raise LabelDictionaryError("invalid label dictionary JSON") from exc

  if not isinstance(document, dict):
    raise LabelDictionaryError("label dictionary must be a JSON object")
  if set(document) != _LABEL_DICTIONARY_KEYS:
    raise LabelDictionaryError("label dictionary has unsupported fields")
  schema_version = document.get("schema_version")
  if isinstance(schema_version, bool) or schema_version != LABEL_DICTIONARY_SCHEMA_VERSION:
    raise LabelDictionaryError(f"unsupported label dictionary schema version: {schema_version!r}")
  metadata_payload = document.get("metadata")
  if not isinstance(metadata_payload, dict):
    raise LabelDictionaryError("label dictionary metadata must be a JSON object")
  if set(metadata_payload) != _LABEL_METADATA_KEYS:
    raise LabelDictionaryError("label dictionary metadata has unsupported fields")

  try:
    metadata = _LABEL_METADATA_ADAPTER.validate_json(
      json.dumps(metadata_payload, ensure_ascii=False, allow_nan=False),
      strict=True,
    )
  except (TypeError, ValueError, ValidationError) as exc:
    raise LabelDictionaryError("label dictionary metadata is invalid") from exc
  validate_label_metadata(metadata)
  return metadata


def save_label_metadata(path: Path, metadata: LabelMetadata, *, replace: bool) -> None:
  """Atomically write a label dictionary without creating parent directories."""
  normalized = path.expanduser()
  if normalized.exists() and not replace:
    raise FileExistsError(normalized)

  serialized = serialize_label_metadata(metadata)
  temporary_path: Path | None = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w",
      encoding="utf-8",
      dir=normalized.parent,
      prefix=f".{normalized.name}.",
      suffix=".tmp",
      delete=False,
    ) as temporary_file:
      temporary_path = Path(temporary_file.name)
      temporary_file.write(serialized)
      temporary_file.flush()
      os.fsync(temporary_file.fileno())
    if replace:
      os.replace(temporary_path, normalized)
    else:
      try:
        os.link(temporary_path, normalized)
      except FileExistsError:
        raise
      finally:
        temporary_path.unlink(missing_ok=True)
    temporary_path = None
  finally:
    if temporary_path is not None:
      try:
        temporary_path.unlink()
      except OSError:
        pass


def load_label_metadata(path: Path) -> LabelMetadata:
  """Read one UTF-8 label dictionary from disk."""
  try:
    text = path.expanduser().read_text(encoding="utf-8")
  except (OSError, UnicodeError):
    raise
  return deserialize_label_metadata(text)


def validate_label_metadata(metadata: LabelMetadata) -> None:
  """Reject ambiguous or non-finite metadata before it crosses an I/O boundary."""
  variable_names = tuple(name for name, _ in metadata.variable_labels)
  if any(not name for name in variable_names) or len(set(variable_names)) != len(variable_names):
    raise LabelDictionaryError("label dictionary has duplicate or empty variable labels")

  set_names = tuple(value_set.name for value_set in metadata.value_sets)
  if any(not name for name in set_names) or len(set(set_names)) != len(set_names):
    raise LabelDictionaryError("label dictionary has duplicate or empty value-label sets")

  attachment_variables = tuple(variable for variable, _ in metadata.attachments)
  if any(not variable for variable in attachment_variables):
    raise LabelDictionaryError("label dictionary has an empty attachment variable")
  if len(set(attachment_variables)) != len(attachment_variables):
    raise LabelDictionaryError("label dictionary has duplicate variable attachments")
  known_sets = set(set_names)
  if any(set_name not in known_sets for _, set_name in metadata.attachments):
    raise LabelDictionaryError("label dictionary attachment references an unknown value-label set")

  for value_set in metadata.value_sets:
    seen_values: set[int | float | str] = set()
    for value, _ in value_set.mappings:
      if isinstance(value, bool):
        raise LabelDictionaryError("label dictionary values must be numbers or strings")
      if isinstance(value, float) and not math.isfinite(value):
        raise LabelDictionaryError("label dictionary values must be finite")
      if value in seen_values:
        raise LabelDictionaryError(
          f"label dictionary has duplicate values in set: {value_set.name}"
        )
      seen_values.add(value)


def _reject_json_constant(value: str) -> None:
  raise ValueError(value)

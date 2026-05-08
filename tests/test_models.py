import pytest
from pydantic import ValidationError

from tabdat.models import CommandOption, HeadCommand, KeepCommand, UseCommand


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

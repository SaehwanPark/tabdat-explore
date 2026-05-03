import pytest
from pydantic import ValidationError

from tabdat.models import CommandOption, HeadCommand, KeepCommand, UseCommand


@pytest.mark.parametrize(
  ("factory", "kwargs"),
  [
    (HeadCommand, {"limit": "5"}),
    (UseCommand, {"path": "data.parquet"}),
    (KeepCommand, {"variables": ["age"]}),
    (CommandOption, {"name": 1}),
  ],
)
def test_models_reject_invalid_runtime_types(factory: type, kwargs: dict[str, object]) -> None:
  with pytest.raises(ValidationError):
    factory(**kwargs)

from pathlib import Path

import pytest

from tabdat.config import load_config
from tabdat.errors import TabDatError


def test_load_config_reports_unreadable_files(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  config_path = tmp_path / "tabdat.toml"
  config_path.write_text('graph_format = "svg"\n', encoding="utf-8")

  def fail_read_text(self: Path, *, encoding: str) -> str:
    raise OSError("permission denied")

  monkeypatch.setattr(Path, "read_text", fail_read_text)

  with pytest.raises(TabDatError, match="config file could not be read"):
    load_config(config_path)

from pathlib import Path

import pytest

from tabdat.config import find_default_config_path, load_config, load_default_config
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


def test_find_default_config_path_prefers_project_local_file(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()
  project_config = project_dir / ".tabdat.toml"
  project_config.write_text('graph_format = "png"\n', encoding="utf-8")
  xdg_home = tmp_path / "xdg"
  xdg_config = xdg_home / "tabdat" / "config.toml"
  xdg_config.parent.mkdir(parents=True)
  xdg_config.write_text('graph_format = "svg"\n', encoding="utf-8")

  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

  assert find_default_config_path() == project_config


def test_find_default_config_path_falls_back_to_xdg_config(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()
  xdg_home = tmp_path / "xdg"
  xdg_config = xdg_home / "tabdat" / "config.toml"
  xdg_config.parent.mkdir(parents=True)
  xdg_config.write_text('graph_format = "png"\n', encoding="utf-8")

  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

  assert find_default_config_path() == xdg_config


def test_find_default_config_path_returns_none_when_no_default_exists(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()

  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "missing-xdg"))

  assert find_default_config_path() is None


def test_load_default_config_uses_xdg_fallback(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  project_dir = tmp_path / "project"
  project_dir.mkdir()
  xdg_home = tmp_path / "xdg"
  artifact_dir = tmp_path / "artifacts"
  xdg_config = xdg_home / "tabdat" / "config.toml"
  xdg_config.parent.mkdir(parents=True)
  xdg_config.write_text(
    f'graph_format = "png"\nartifact_dir = "{artifact_dir}"\ngraph_open = false\n',
    encoding="utf-8",
  )

  monkeypatch.chdir(project_dir)
  monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

  config = load_default_config()

  assert config.graph_format == "png"
  assert config.artifact_dir == artifact_dir
  assert config.graph_open is False

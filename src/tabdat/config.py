"""Runtime configuration for TabDat sessions."""

import os
import tomllib
from pathlib import Path
from typing import Literal, cast

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from tabdat.errors import TabDatError

_MODEL_CONFIG = ConfigDict(strict=True)


@dataclass(frozen=True, config=_MODEL_CONFIG)
class TabDatConfig:
  graph_format: Literal["svg", "png"] = "svg"
  artifact_dir: Path = Path("artifacts")
  graph_open: bool = True


def load_config(path: Path) -> TabDatConfig:
  normalized = path.expanduser()
  if not normalized.exists():
    raise TabDatError(f"config file not found: {path}")
  if not normalized.is_file():
    raise TabDatError(f"config path is not a file: {path}")
  try:
    data = tomllib.loads(normalized.read_text(encoding="utf-8"))
  except OSError as exc:
    raise TabDatError(f"config file could not be read: {path}") from exc
  except UnicodeDecodeError as exc:
    raise TabDatError(f"config file is not valid UTF-8: {path}") from exc
  except tomllib.TOMLDecodeError as exc:
    raise TabDatError(f"config file is not valid TOML: {path}") from exc
  return config_from_mapping(data)


def load_default_config() -> TabDatConfig:
  default_path = find_default_config_path()
  if default_path is not None:
    return load_config(default_path)
  return TabDatConfig()


def find_default_config_path() -> Path | None:
  project_path = Path.cwd() / ".tabdat.toml"
  if project_path.exists():
    return project_path

  xdg_path = _xdg_config_path()
  if xdg_path.exists():
    return xdg_path
  return None


def config_from_mapping(data: dict[str, object]) -> TabDatConfig:
  allowed = {"graph_format", "artifact_dir", "graph_open"}
  unknown = set(data) - allowed
  if unknown:
    raise TabDatError(f"unknown config key: {', '.join(sorted(unknown))}")
  config = TabDatConfig()
  for key, value in data.items():
    config = set_config_value(config, key, value)
  return config


def set_config_value(config: TabDatConfig, name: str, value: object) -> TabDatConfig:
  if name == "graph_format":
    if value not in {"svg", "png"}:
      raise TabDatError("graph_format must be svg or png")
    graph_format = cast(Literal["svg", "png"], value)
    return TabDatConfig(graph_format, config.artifact_dir, config.graph_open)
  if name == "artifact_dir":
    if not isinstance(value, str) or not value:
      raise TabDatError("artifact_dir must be a non-empty path")
    return TabDatConfig(config.graph_format, Path(value), config.graph_open)
  if name == "graph_open":
    if isinstance(value, str):
      normalized = value.lower()
      if normalized == "on":
        parsed = True
      elif normalized == "off":
        parsed = False
      else:
        raise TabDatError("graph_open must be on or off")
    elif isinstance(value, bool):
      parsed = value
    else:
      raise TabDatError("graph_open must be on or off")
    return TabDatConfig(config.graph_format, config.artifact_dir, parsed)
  raise TabDatError(f"unknown config key: {name}")


def _xdg_config_path() -> Path:
  config_home = os.environ.get("XDG_CONFIG_HOME")
  if config_home:
    return Path(config_home).expanduser() / "tabdat" / "config.toml"
  return Path.home() / ".config" / "tabdat" / "config.toml"

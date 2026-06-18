"""Runtime configuration for TabDat sessions.

Manages loading, parsing, and validating user configuration settings. Configuration
keys control visualization formatting, automatic opening of plots, and artifact directories.

Configuration lookup precedence (highest to lowest):
  1. Local project configuration file: `./.tabdat.toml` (in the current working directory).
  2. Global user configuration file: `~/.config/tabdat/config.toml` (or custom XDG path).
  3. Default fallback values defined in `TabDatConfig`.
"""

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
  """Session configuration settings.

  Attributes:
    graph_format: The file format for exported visualizations ('svg' or 'png').
    artifact_dir: Directory path where visualizations and exported files are saved.
    graph_open: If True, automatically launches the system default application or
      browser to view newly generated visual plots.
  """

  graph_format: Literal["svg", "png"] = "svg"
  artifact_dir: Path = Path("artifacts")
  graph_open: bool = True


def load_config(path: Path) -> TabDatConfig:
  """Load and parse configuration values from a specific TOML file.

  Expands user home directory shortcuts (e.g., `~`) and decodes TOML contents.
  Validates configuration keys and values against the allowed set.

  Args:
    path: The file path to the TOML configuration.

  Returns:
    A validated TabDatConfig instance.

  Raises:
    TabDatError: If the file does not exist, is not a file, cannot be read, contains
      invalid TOML syntax, or contains invalid/unknown configuration keys.
  """
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
  """Load configuration using the standard search cascade.

  Attempts to discover `.tabdat.toml` locally, falling back to XDG config locations,
  and finally returning default settings if no configuration file is found.

  Returns:
    The resolved session configuration.
  """
  default_path = find_default_config_path()
  if default_path is not None:
    return load_config(default_path)
  return TabDatConfig()


def find_default_config_path() -> Path | None:
  """Resolve the path of the default configuration file if it exists.

  Checks first for a local `.tabdat.toml` in the current working directory to allow
  project-specific overrides, then checks the global user XDG path.

  Returns:
    The resolved Path object if a config file is found, otherwise None.
  """
  project_path = Path.cwd() / ".tabdat.toml"
  if project_path.exists():
    return project_path

  xdg_path = _xdg_config_path()
  if xdg_path.exists():
    return xdg_path
  return None


def config_from_mapping(data: dict[str, object]) -> TabDatConfig:
  """Construct a TabDatConfig from a generic dictionary.

  Filters for unknown keys before applying mutations to avoid silent failures or
  carrying unsupported options.

  Args:
    data: Raw dictionary mapping configuration keys to their configured values.

  Returns:
    A fully validated TabDatConfig instance.

  Raises:
    TabDatError: If the dictionary contains keys not supported by TabDatConfig.
  """
  allowed = {"graph_format", "artifact_dir", "graph_open"}
  unknown = set(data) - allowed
  if unknown:
    raise TabDatError(f"unknown config key: {', '.join(sorted(unknown))}")
  config = TabDatConfig()
  for key, value in data.items():
    config = set_config_value(config, key, value)
  return config


def set_config_value(config: TabDatConfig, name: str, value: object) -> TabDatConfig:
  """Validate and update a single option value, returning a new immutable configuration instance.

  Coerces configuration input strings (e.g., mapping 'on'/'off' to boolean states
  for graph auto-opening) and validates constraints.

  Args:
    config: The current base TabDatConfig.
    name: The name of the configuration key to update.
    value: The new value to assign.

  Returns:
    A new updated TabDatConfig instance.

  Raises:
    TabDatError: If the value is of an invalid type or fails validation constraints
      for the specified configuration option.
  """
  if name == "graph_format":
    if value not in {"svg", "png"}:
      raise TabDatError("graph_format must be svg or png")
    graph_format = cast(Literal["svg", "png"], value)
    return TabDatConfig(graph_format, config.artifact_dir, config.graph_open)
  if name == "artifact_dir":
    if isinstance(value, Path):
      resolved_value = value
    elif isinstance(value, str) and value:
      resolved_value = Path(value)
    else:
      raise TabDatError("artifact_dir must be a non-empty path")
    return TabDatConfig(config.graph_format, resolved_value, config.graph_open)
  if name == "graph_open":
    # Parse string representations (e.g., standard 'on'/'off') into a boolean state.
    if isinstance(value, str):
      normalized = value.lower()
      if normalized == "on":
        parsed = True
      elif normalized == "off":
        parsed = False
      else:
        raise TabDatError("graph_open must be a boolean or 'on'/'off' string")
    elif isinstance(value, bool):
      parsed = value
    else:
      raise TabDatError("graph_open must be a boolean or 'on'/'off' string")
    return TabDatConfig(config.graph_format, config.artifact_dir, parsed)
  raise TabDatError(f"unknown config key: {name}")


def _xdg_config_path() -> Path:
  """Resolve the standard user-level XDG configuration path for TabDat.

  Utilizes the `XDG_CONFIG_HOME` environment variable if defined, defaulting
  to standard Unix `~/.config/tabdat/config.toml` structure.

  Returns:
    The target Path where the global config file is expected.
  """
  config_home = os.environ.get("XDG_CONFIG_HOME")
  if config_home:
    return Path(config_home).expanduser() / "tabdat" / "config.toml"
  return Path.home() / ".config" / "tabdat" / "config.toml"

"""Environment and capability diagnostics for TabDat."""

import importlib.util
import os
import platform
import shutil
import sys
from importlib import metadata

from tabdat.models import DoctorCapabilityItem, DoctorResult


def _get_package_version(pkg_name: str) -> str | None:
  """Safely determine the installed version of a package without hard errors."""
  try:
    return metadata.version(pkg_name)
  except metadata.PackageNotFoundError:
    pass
  try:
    spec = importlib.util.find_spec(pkg_name)
    if spec is not None:
      mod = importlib.import_module(pkg_name)
      version = getattr(mod, "__version__", None)
      if version is not None:
        return str(version)
      return "installed"
  except Exception:
    return None
  return None


def _check_simple_capability(
  name: str, pkg_names: tuple[str, ...], *, display_prefix: str = ""
) -> DoctorCapabilityItem:
  """Check a capability backed by one or more Python packages."""
  versions: list[str] = []
  missing: list[str] = []
  for pkg in pkg_names:
    ver = _get_package_version(pkg)
    if ver is not None:
      versions.append(f"{pkg} {ver}")
    else:
      missing.append(pkg)

  if versions:
    avail = len(missing) == 0
    details = ", ".join(versions)
    if missing:
      details = f"{details} (missing: {', '.join(missing)})"
    return DoctorCapabilityItem(
      name=name,
      available=avail,
      version=versions[0].split()[1] if len(versions) == 1 else None,
      details=details,
    )
  return DoctorCapabilityItem(
    name=name,
    available=False,
    version=None,
    details=f"not installed ({', '.join(pkg_names)})",
  )


def _check_r_capability() -> DoctorCapabilityItem:
  """Check R integration capability (rpy2 + system R runtime)."""
  rpy2_ver = _get_package_version("rpy2")
  r_bin = shutil.which("R")
  r_home = os.environ.get("R_HOME")

  if rpy2_ver is not None and (r_bin is not None or r_home is not None):
    details = (
      f"rpy2 {rpy2_ver}, R binary at {r_bin}" if r_bin else f"rpy2 {rpy2_ver}, R_HOME={r_home}"
    )
    return DoctorCapabilityItem(
      name="R",
      available=True,
      version=rpy2_ver,
      details=details,
    )
  if rpy2_ver is not None:
    return DoctorCapabilityItem(
      name="R",
      available=False,
      version=rpy2_ver,
      details=f"rpy2 {rpy2_ver} installed, but R binary / R_HOME not found",
    )
  return DoctorCapabilityItem(
    name="R",
    available=False,
    version=None,
    details="rpy2 not installed",
  )


def _get_tabdat_version() -> str:
  for name in ("tabdat-explore-dev", "tabdat-explore", "tabdat"):
    try:
      return metadata.version(name)
    except metadata.PackageNotFoundError:
      pass
  return "0.23.0"


def inspect_environment() -> DoctorResult:
  """Inspect the environment and return a structured DoctorResult."""
  version = _get_tabdat_version()

  core_items = (
    _check_simple_capability("DuckDB", ("duckdb",)),
    _check_simple_capability("PyArrow", ("pyarrow",)),
    _check_simple_capability("Polars", ("polars",)),
    _check_simple_capability("Plotting", ("altair", "matplotlib")),
  )

  stats_items = (
    _check_simple_capability("statsmodels", ("statsmodels",)),
    _check_simple_capability("linearmodels", ("linearmodels",)),
    _check_simple_capability("scipy", ("scipy",)),
  )

  optional_items = (
    _check_simple_capability("ML", ("sklearn",)),
    _check_simple_capability("Bayesian", ("bambi",)),
    _check_simple_capability("Spatial", ("spreg", "libpysal")),
    _check_r_capability(),
  )

  system_items = (
    DoctorCapabilityItem(
      name="Python",
      available=True,
      version=platform.python_version(),
      details=sys.version.splitlines()[0],
    ),
    DoctorCapabilityItem(
      name="Platform",
      available=True,
      version=platform.system(),
      details=f"{platform.system()} {platform.release()} ({platform.machine()})",
    ),
    DoctorCapabilityItem(
      name="Executable",
      available=True,
      version=None,
      details=sys.executable,
    ),
  )

  return DoctorResult(
    version=version,
    core=core_items,
    statistics=stats_items,
    optional=optional_items,
    system=system_items,
  )

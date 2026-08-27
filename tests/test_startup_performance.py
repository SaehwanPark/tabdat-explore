"""Tests verifying zero heavy third-party statistical imports on startup."""

import subprocess
import sys


def test_zero_heavy_modules_on_cli_import() -> None:
  code = """
import sys
import tabdat.cli

heavy_modules = [
  'statsmodels',
  'spreg',
  'libpysal',
  'linearmodels',
  'sklearn',
  'bambi',
  'rpy2',
  'altair',
  'matplotlib',
]
loaded = [m for m in heavy_modules if m in sys.modules]
if loaded:
    print(f"FAILED: Found eager heavy modules in sys.modules: {loaded}")
    sys.exit(1)
print("OK")
"""
  res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
  assert res.returncode == 0, f"Import regression detected:\n{res.stdout}\n{res.stderr}"


def test_cli_version_flag() -> None:
  from tabdat import __version__

  res = subprocess.run(["uv", "run", "tabdat", "--version"], capture_output=True, text=True)
  assert res.returncode == 0
  assert f"tabdat {__version__}" in res.stdout

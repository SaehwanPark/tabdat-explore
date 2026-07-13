"""Smoke-test packaged help resources through a freshly built wheel."""

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_SMOKE_CODE = """
import contextlib
import io
import json

from tabdat.cli import main

stdout = io.StringIO()
stderr = io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
  exit_code = main(["--json", "--help-topic", "SuMmArIzE"])
envelope = json.loads(stdout.getvalue())
assert exit_code == 0
assert stderr.getvalue() == ""
assert envelope["result_type"] == "HelpTopicResult"
assert envelope["data"]["help_topic"] == "summarize"
assert envelope["data"]["text"].endswith("\\n")
"""


def main() -> None:
  with TemporaryDirectory() as temporary_directory:
    wheel_directory = Path(temporary_directory)
    subprocess.run(
      ["uv", "build", "--wheel", "--out-dir", str(wheel_directory)],
      cwd=_REPOSITORY_ROOT,
      check=True,
    )
    wheels = tuple(wheel_directory.glob("*.whl"))
    if len(wheels) != 1:
      raise RuntimeError(f"expected one wheel, found {len(wheels)}")

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(wheels[0])
    subprocess.run(
      [sys.executable, "-c", _SMOKE_CODE],
      cwd=wheel_directory,
      env=environment,
      check=True,
    )


if __name__ == "__main__":
  main()

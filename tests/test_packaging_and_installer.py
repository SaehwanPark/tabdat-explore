"""Tests for packaging, GitHub Actions CI/CD workflows, and the install.sh script."""

import subprocess
import zipfile
from pathlib import Path


def test_install_script_syntax_and_contents() -> None:
  install_script = Path("scripts/install.sh")
  assert install_script.exists()

  # Test POSIX shell syntax validity
  res = subprocess.run(["sh", "-n", str(install_script)], capture_output=True, text=True)
  assert res.returncode == 0, f"install.sh syntax error: {res.stderr}"

  content = install_script.read_text(encoding="utf-8")
  assert "uv tool install" in content
  assert "tabdat doctor" in content
  assert "Linux|Darwin" in content


def test_github_actions_workflows_exist() -> None:
  ci_workflow = Path(".github/workflows/ci.yml")
  release_workflow = Path(".github/workflows/release.yml")

  assert ci_workflow.exists()
  assert release_workflow.exists()

  ci_text = ci_workflow.read_text(encoding="utf-8")
  assert "pytest" in ci_text
  assert "basedpyright" in ci_text
  assert "check_docs_alignment.py" in ci_text
  assert "wheel-smoke" in ci_text

  release_text = release_workflow.read_text(encoding="utf-8")
  assert "action-gh-release" in release_text
  assert "SHA256SUMS.txt" in release_text


def test_wheel_package_contains_topics_and_entrypoints(tmp_path: Path) -> None:
  dist_dir = Path("dist")
  wheels = list(dist_dir.glob("*.whl")) if dist_dir.exists() else []
  if not wheels:
    subprocess.run(
      ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
      check=True,
      capture_output=True,
    )
    wheels = list(tmp_path.glob("*.whl"))

  assert len(wheels) >= 1, "No built wheel found"

  wheel_path = wheels[0]
  with zipfile.ZipFile(wheel_path, "r") as zf:
    names = set(zf.namelist())
    assert "tabdat/cli.py" in names
    assert "tabdat/doctor.py" in names
    assert "tabdat/help/topics/describe.md" in names
    assert "tabdat/help/topics/doctor.md" in names
    assert "tabdat/help/topics/summarize.md" in names

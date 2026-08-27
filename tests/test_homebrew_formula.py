"""Tests for Homebrew formula syntax and ADR documentation."""

from pathlib import Path


def test_homebrew_formula_file_validity() -> None:
  formula_path = Path("Formula/tabdat.rb")
  assert formula_path.exists()

  content = formula_path.read_text(encoding="utf-8")
  assert "class Tabdat < Formula" in content
  assert 'desc "Terminal-native exploratory data analysis tool for modern tabular data"' in content
  assert 'homepage "https://github.com/SaehwanPark/tabdat-explore"' in content
  assert 'license "AGPL-3.0-or-later"' in content
  assert 'depends_on "python@3.13"' in content
  assert "def install" in content
  assert "virtualenv_install_with_resources" in content
  assert "test do" in content
  assert "tabdat doctor" in content


def test_distribution_adr_exists_and_covers_matrix() -> None:
  adr_path = Path("docs/adr/0001-distribution-and-packaging-strategy.md")
  assert adr_path.exists()

  content = adr_path.read_text(encoding="utf-8")
  assert "ADR 0001" in content
  assert "**Status**: Accepted" in content
  assert "uv tool" in content
  assert "Homebrew Formula" in content
  assert "PyInstaller" in content
  assert "tabdat doctor" in content

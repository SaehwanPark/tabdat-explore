"""Test case to ensure markdown documentation links and command alignment remain intact."""

import sys
from pathlib import Path

# Add repo root to python path to import the scripts module
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.check_docs_alignment import (  # noqa: E402
  check_command_documentation,
  check_help_topic_alignment,
  check_markdown_links,
)


def test_markdown_links():
  """Check that all relative local markdown links resolve to valid files/anchors."""
  errors = check_markdown_links()
  assert not errors, "Broken markdown links found:\n" + "\n".join(errors)


def test_command_documentation():
  """Check that all executable commands are documented in docs/command-reference.md."""
  errors = check_command_documentation()
  assert not errors, "Command documentation mismatch found:\n" + "\n".join(errors)


def test_help_topic_alignment():
  """Check that all executable commands have matching help topics and vice versa."""
  errors = check_help_topic_alignment()
  assert not errors, "Help topic alignment mismatch found:\n" + "\n".join(errors)

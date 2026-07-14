#!/usr/bin/env python3
"""Script to verify alignment of markdown documents, links, and command registries."""

import os
import re
import sys
from pathlib import Path

# Add src to path so we can import tabdat modules
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
  from tabdat.help import available_help_topics
  from tabdat.parser import _EXECUTABLE_COMMANDS
except ImportError as e:
  print(f"Error: Could not import tabdat packages: {e}", file=sys.stderr)
  sys.exit(1)


def generate_anchor_id(header_text: str) -> str:
  """Convert a markdown header text to a GitHub-compatible anchor ID."""
  # Remove markdown formatting characters (like backticks, asterisks)
  text = re.sub(r"[`*_]", "", header_text.strip().lower())
  # Replace spaces and other non-alphanumeric chars with hyphens
  text = re.sub(r"[^a-z0-9\s-]", "", text)
  text = re.sub(r"\s+", "-", text)
  return text


def find_anchors_in_file(file_path: Path) -> set[str]:
  """Scan a file for markdown headers and return their anchor IDs."""
  anchors = set()
  try:
    content = file_path.read_text(encoding="utf-8")
    for line in content.splitlines():
      match = re.match(r"^(#{1,6})\s+(.+)$", line)
      if match:
        header_text = match.group(2)
        anchors.add(generate_anchor_id(header_text))
  except Exception as e:
    print(f"Warning: Failed to read {file_path} for headers: {e}")
  return anchors


def check_markdown_links() -> list[str]:
  """Verify that all relative local markdown links resolve to valid files and anchors."""
  errors = []
  exclude_dirs = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "_workspace"}
  markdown_files = []

  for root, dirs, files in os.walk(REPO_ROOT):
    # Prune excluded directories
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
      if file.endswith(".md"):
        markdown_files.append(Path(root) / file)

  # Pre-cache anchors for all markdown files to avoid re-reading
  file_anchors = {}
  for md_file in markdown_files:
    file_anchors[md_file.resolve()] = find_anchors_in_file(md_file)

  # Link regex: match [text](url) where url does not start with http/https/mailto
  # Also handle potential anchors like [text](#anchor) or [text](file.md#anchor)
  link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

  for md_file in markdown_files:
    try:
      content = md_file.read_text(encoding="utf-8")
      for line_num, line in enumerate(content.splitlines(), start=1):
        for match in link_pattern.finditer(line):
          label, url = match.groups()
          # Clean url from spaces, quotes, etc., if any
          url = url.strip()

          # Skip remote links
          if url.startswith(("http://", "https://", "mailto:", "file://")):
            continue

          # Skip pure anchors in other files (not starting with #) unless we handle them
          target_path_str = url
          anchor = ""
          if "#" in url:
            target_path_str, anchor = url.split("#", 1)

          # If the path is empty, it refers to the current file
          if not target_path_str:
            target_file = md_file
          else:
            target_file = (md_file.parent / target_path_str).resolve()

          # Check file existence
          if not target_file.exists():
            errors.append(
              f"[{md_file.relative_to(REPO_ROOT)}:{line_num}] "
              f"Broken link '{url}': target file does not exist: "
              f"{target_path_str}"
            )
            continue

          # Check anchor existence if specified
          if anchor:
            anchors_in_target = file_anchors.get(target_file)
            if anchors_in_target is None:
              anchors_in_target = find_anchors_in_file(target_file)
              file_anchors[target_file] = anchors_in_target

            if anchor not in anchors_in_target:
              errors.append(
                f"[{md_file.relative_to(REPO_ROOT)}:{line_num}] "
                f"Broken anchor in '{url}': anchor '#{anchor}' "
                f"not found in target file"
              )
    except Exception as e:
      errors.append(f"Failed to process {md_file.relative_to(REPO_ROOT)}: {e}")

  return errors


def check_command_documentation() -> list[str]:
  """Verify that all executable commands are documented in docs/command-reference.md."""
  errors = []
  cmd_ref_path = REPO_ROOT / "docs" / "command-reference.md"
  if not cmd_ref_path.exists():
    return ["Required document docs/command-reference.md does not exist!"]

  try:
    content = cmd_ref_path.read_text(encoding="utf-8")
  except Exception as e:
    return [f"Failed to read docs/command-reference.md: {e}"]

  # Look for backticked commands in docs/command-reference.md
  # e.g., `use`, `describe`
  documented_commands = set(re.findall(r"`([^`\s:]+)`|`([^`\s:]+):`", content))
  # Flatten and filter out None values and sanitize
  flat_documented = set()
  for item in documented_commands:
    for cmd in item:
      if cmd:
        flat_documented.add(cmd.lower())

  # Check that each executable command is documented
  for cmd in _EXECUTABLE_COMMANDS:
    if cmd not in flat_documented:
      errors.append(
        f"Command '{cmd}' is in _EXECUTABLE_COMMANDS but "
        "not documented in docs/command-reference.md"
      )

  return errors


def check_help_topic_alignment() -> list[str]:
  """Verify help topic mapping between executable commands and topics."""
  errors = []
  help_topics = set(available_help_topics())

  # These commands do not have separate help files as per design/specification
  no_help_needed = {"test", "lincom", "ttest"}

  # Verify executable commands have help topics
  for cmd in _EXECUTABLE_COMMANDS:
    if cmd in no_help_needed:
      continue
    # Special commands might have slightly different topic names
    topic_name = cmd
    if cmd == "exit" or cmd == "quit":
      pass  # they have exit.md and quit.md

    if topic_name not in help_topics:
      errors.append(
        f"Command '{cmd}' is in _EXECUTABLE_COMMANDS but has no help topic file: {cmd}.md"
      )

  # Verify all help topics correspond to actual commands/subcommands.
  # Note: some help files are helper subtopics (like bayes_prefix,
  # estat_report) or represent prefixes (by).
  valid_subtopics = {"bayes_prefix", "estat_report", "by"}

  for topic in help_topics:
    if topic in valid_subtopics:
      continue
    if topic not in _EXECUTABLE_COMMANDS:
      errors.append(
        f"Help topic file '{topic}.md' exists but '{topic}' is not in _EXECUTABLE_COMMANDS"
      )

  return errors


def main() -> None:
  print("Running markdown documentation and command alignment checks...")

  link_errors = check_markdown_links()
  if link_errors:
    print(f"\n--- Found {len(link_errors)} Broken Markdown Links/Anchors ---")
    for err in link_errors:
      print(f"  {err}")
  else:
    print("✓ All markdown links and anchors are valid.")

  doc_errors = check_command_documentation()
  if doc_errors:
    print(f"\n--- Found {len(doc_errors)} Command Documentation Errors ---")
    for err in doc_errors:
      print(f"  {err}")
  else:
    print("✓ All executable commands are documented in command-reference.md.")

  help_errors = check_help_topic_alignment()
  if help_errors:
    print(f"\n--- Found {len(help_errors)} Help Topic Errors ---")
    for err in help_errors:
      print(f"  {err}")
  else:
    print("✓ Help topic files and executable commands are fully aligned.")

  all_errors = link_errors + doc_errors + help_errors
  if all_errors:
    print(f"\nVerification FAILED with {len(all_errors)} total errors.")
    sys.exit(1)

  print("\nVerification PASSED successfully!")
  sys.exit(0)


if __name__ == "__main__":
  main()

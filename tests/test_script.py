from pathlib import Path

import pytest

from tabdat.script import ScriptCommand, ScriptError, parse_script, read_script


def test_parse_script_ignores_blank_lines_and_whole_line_comments() -> None:
  assert parse_script(
    """
    # load data

    use patients.parquet
      # inspect data
    describe
    """
  ) == (
    ScriptCommand("    use patients.parquet", 4),
    ScriptCommand("    describe", 6),
  )


def test_parse_script_preserves_multiline_sql_command() -> None:
  assert parse_script('use patients.parquet\nsql """\nselect *\nfrom active\n"""\ncount\n') == (
    ScriptCommand("use patients.parquet", 1),
    ScriptCommand('sql """\nselect *\nfrom active\n"""', 2),
    ScriptCommand("count", 6),
  )


def test_parse_script_rejects_unterminated_multiline_sql() -> None:
  with pytest.raises(ScriptError, match='<script>:2: sql multiline query is missing closing """'):
    parse_script('use patients.parquet\nsql """\nselect *\n')


def test_read_script_reports_missing_file(tmp_path: Path) -> None:
  missing = tmp_path / "missing.td"

  with pytest.raises(ScriptError, match="script file not found"):
    read_script(missing)

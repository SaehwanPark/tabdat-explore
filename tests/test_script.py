from pathlib import Path

import pytest

from tabdat.script import (
  LetDirective,
  ScriptCommand,
  ScriptContext,
  ScriptError,
  SeedDirective,
  expand_script_macros,
  parse_script,
  parse_script_directive,
  read_script,
)


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


def test_expand_script_macros_substitutes_defined_values(tmp_path: Path) -> None:
  context = ScriptContext(macros={"data": "patients.parquet", "condition": "age >= 18"})

  expanded = expand_script_macros(
    "use $data\nkeep if $condition",
    context,
    path=tmp_path / "analysis.td",
    line=2,
  )

  assert expanded == "use patients.parquet\nkeep if age >= 18"


def test_expand_script_macros_rejects_undefined_reference(tmp_path: Path) -> None:
  context = ScriptContext.empty()

  with pytest.raises(ScriptError, match="analysis.td:3: undefined macro: data"):
    expand_script_macros("use $data", context, path=tmp_path / "analysis.td", line=3)


def test_parse_script_seed_directive() -> None:
  context = ScriptContext.empty()

  assert parse_script_directive("seed 123", context, path=Path("analysis.td"), line=1) == (
    SeedDirective(123)
  )


def test_parse_script_seed_directive_rejects_invalid_value() -> None:
  context = ScriptContext.empty()

  with pytest.raises(ScriptError, match="analysis.td:1: seed expects an integer"):
    parse_script_directive("seed 1.5", context, path=Path("analysis.td"), line=1)


def test_parse_script_let_directive() -> None:
  context = ScriptContext.empty()

  assert parse_script_directive(
    "let data = patients.parquet",
    context,
    path=Path("analysis.td"),
    line=1,
  ) == LetDirective("data", "patients.parquet")


def test_parse_script_let_directive_allows_previous_macro_references() -> None:
  context = ScriptContext(macros={"root": "data"})
  expanded = expand_script_macros(
    "let file = $root/patients.parquet",
    context,
    path=Path("analysis.td"),
    line=2,
  )

  assert parse_script_directive(expanded, context, path=Path("analysis.td"), line=2) == (
    LetDirective("file", "data/patients.parquet")
  )


def test_parse_script_let_directive_rejects_invalid_syntax() -> None:
  context = ScriptContext.empty()

  with pytest.raises(ScriptError, match="analysis.td:1: let expects syntax"):
    parse_script_directive("let data patients.parquet", context, path=Path("analysis.td"), line=1)


def test_parse_script_let_directive_rejects_invalid_name() -> None:
  context = ScriptContext.empty()

  with pytest.raises(ScriptError, match="analysis.td:1: macro name must be an identifier: 1data"):
    parse_script_directive(
      "let 1data = patients.parquet",
      context,
      path=Path("analysis.td"),
      line=1,
    )


def test_parse_script_let_directive_rejects_empty_value() -> None:
  context = ScriptContext.empty()

  with pytest.raises(ScriptError, match="analysis.td:1: macro value cannot be empty: data"):
    parse_script_directive("let data = ", context, path=Path("analysis.td"), line=1)


def test_parse_script_let_directive_rejects_duplicate_name() -> None:
  context = ScriptContext(macros={"data": "patients.parquet"})

  with pytest.raises(ScriptError, match="analysis.td:1: macro already defined: data"):
    parse_script_directive(
      "let data = other.parquet",
      context,
      path=Path("analysis.td"),
      line=1,
    )

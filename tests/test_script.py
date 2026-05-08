from pathlib import Path

import pytest

from tabdat.script import (
  ElseDirective,
  EndDirective,
  IfDirective,
  LetDirective,
  ScriptBlockState,
  ScriptCommand,
  ScriptContext,
  ScriptError,
  SeedDirective,
  evaluate_script_condition,
  expand_script_macros,
  parse_control_flow_directive,
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


def test_parse_script_control_flow_directives() -> None:
  assert parse_control_flow_directive("if true", path=Path("analysis.td"), line=1) == IfDirective(
    active=True
  )
  assert parse_control_flow_directive("else", path=Path("analysis.td"), line=2) == ElseDirective()
  assert parse_control_flow_directive("end", path=Path("analysis.td"), line=3) == EndDirective()
  assert parse_control_flow_directive("count", path=Path("analysis.td"), line=4) is None


def test_script_block_state_reports_current_branch_activity() -> None:
  assert ScriptBlockState(start_line=1, condition_active=True).current_branch_active is True
  assert (
    ScriptBlockState(start_line=1, condition_active=True, in_else=True).current_branch_active
    is False
  )
  assert (
    ScriptBlockState(start_line=1, condition_active=False, in_else=True).current_branch_active
    is True
  )


@pytest.mark.parametrize(
  ("condition", "expected"),
  [
    ("true", True),
    ("on", True),
    ("1", True),
    ("false", False),
    ("off", False),
    ("0", False),
    ("duckdb == duckdb", True),
    ("duckdb != polars", True),
    ("duckdb == polars", False),
  ],
)
def test_evaluate_script_condition(condition: str, expected: bool) -> None:
  assert evaluate_script_condition(condition, path=Path("analysis.td"), line=1) is expected


def test_evaluate_script_condition_rejects_unsupported_condition() -> None:
  with pytest.raises(ScriptError, match="analysis.td:1: if condition expects"):
    evaluate_script_condition("duckdb", path=Path("analysis.td"), line=1)


def test_parse_script_control_flow_rejects_missing_condition() -> None:
  with pytest.raises(ScriptError, match="analysis.td:1: if expects a condition"):
    parse_control_flow_directive("if", path=Path("analysis.td"), line=1)

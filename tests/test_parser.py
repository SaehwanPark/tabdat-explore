from pathlib import Path

import pytest

from tabdat.errors import ParseError
from tabdat.models import (
  AppendCommand,
  BarCommand,
  BinaryExpression,
  ByCommand,
  CodebookCommand,
  CollapseCommand,
  CommandOption,
  CountCommand,
  DescribeCommand,
  DropCommand,
  ExitCommand,
  ExportCommand,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HistogramCommand,
  IdentifierExpression,
  JoinCommand,
  KeepCommand,
  NumberExpression,
  PanelCommand,
  ParsedCommand,
  RenameCommand,
  ReplaceCommand,
  ReshapeCommand,
  RunCommand,
  SaveCommand,
  ScatterCommand,
  SelectCommand,
  SetCommand,
  SqlCommand,
  StringExpression,
  SummarizeCommand,
  TabulateCommand,
  TailCommand,
  UseCommand,
)
from tabdat.parser import parse_command, parse_expression


def test_parse_use_command() -> None:
  assert parse_command("use data.parquet") == UseCommand(Path("data.parquet"))
  assert parse_command("use data.parquet, lazy") == UseCommand(
    Path("data.parquet"),
    execution_mode="lazy",
    lazy_engine="duckdb",
  )
  assert parse_command("use data.parquet, lazy engine=duckdb") == UseCommand(
    Path("data.parquet"),
    execution_mode="lazy",
    lazy_engine="duckdb",
  )
  assert parse_command("use data.parquet, lazy engine=polars") == UseCommand(
    Path("data.parquet"),
    execution_mode="lazy",
    lazy_engine="polars",
  )


def test_parse_phase_11_join_command() -> None:
  assert parse_command("join lookup on id") == JoinCommand(
    table_name="lookup",
    keys=("id",),
  )
  assert parse_command("join lookup on firm_id year, how=left suffix(_lookup)") == JoinCommand(
    table_name="lookup",
    keys=("firm_id", "year"),
    how="left",
    suffix="_lookup",
  )


def test_parse_phase_11_append_command() -> None:
  assert parse_command("append followup") == AppendCommand(table_name="followup")


def test_parse_phase_11_reshape_commands() -> None:
  assert parse_command("reshape long income cost, i(id) j(year)") == ReshapeCommand(
    direction="long",
    variables=("income", "cost"),
    identifiers=("id",),
    j_variable="year",
  )
  assert parse_command("reshape wide income cost, i(firm_id person_id) j(year)") == (
    ReshapeCommand(
      direction="wide",
      variables=("income", "cost"),
      identifiers=("firm_id", "person_id"),
      j_variable="year",
    )
  )


def test_parse_phase_11_panel_commands() -> None:
  assert parse_command("panel") == PanelCommand(action="report")
  assert parse_command("panel firm_id year") == PanelCommand(
    action="set",
    id_variable="firm_id",
    time_variable="year",
  )
  assert parse_command("panel clear") == PanelCommand(action="clear")


def test_parse_describe_command() -> None:
  assert parse_command("describe") == DescribeCommand()


def test_parse_summarize_command_with_variables() -> None:
  assert parse_command("summarize age bmi") == SummarizeCommand(("age", "bmi"))


def test_parse_summarize_preserves_punctuated_variable_names() -> None:
  assert parse_command("summarize bmi-zscore cost.2024 x/y") == SummarizeCommand(
    ("bmi-zscore", "cost.2024", "x/y")
  )


def test_parse_summarize_command_without_variables() -> None:
  assert parse_command("summarize") == SummarizeCommand(())


def test_parse_phase_3_inspection_commands() -> None:
  assert parse_command("codebook") == CodebookCommand(())
  assert parse_command("codebook age sex") == CodebookCommand(("age", "sex"))
  assert parse_command("count") == CountCommand()
  assert parse_command("head") == HeadCommand(5)
  assert parse_command("head 10") == HeadCommand(10)
  assert parse_command("head 01") == HeadCommand(1)
  assert parse_command("head 0") == HeadCommand(0)
  assert parse_command("tail") == TailCommand(5)
  assert parse_command("tail 2") == TailCommand(2)
  assert parse_command("tail 000") == TailCommand(0)


def test_parse_summarize_with_if_as_structured_phase_2_command() -> None:
  assert parse_command("summarize age bmi-zscore if age >= 18") == ParsedCommand(
    name="summarize",
    arguments=("age", "bmi-zscore"),
    condition=BinaryExpression(
      left=IdentifierExpression("age"),
      operator=">=",
      right=NumberExpression(18),
    ),
  )


def test_parse_summarize_with_options_as_structured_phase_2_command() -> None:
  assert parse_command("summarize age bmi, detail limit=10") == ParsedCommand(
    name="summarize",
    arguments=("age", "bmi"),
    options=(
      CommandOption("detail", True),
      CommandOption("limit", 10),
    ),
  )


def test_parse_condition_and_options() -> None:
  assert parse_command('summarize age if sex == "F", detail') == ParsedCommand(
    name="summarize",
    arguments=("age",),
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
    options=(CommandOption("detail", True),),
  )


def test_parse_phase_3_transformation_commands() -> None:
  assert parse_command("keep age bmi") == KeepCommand(variables=("age", "bmi"))
  assert parse_command("keep if age >= 18") == KeepCommand(
    condition=BinaryExpression(
      left=IdentifierExpression("age"),
      operator=">=",
      right=NumberExpression(18),
    ),
  )
  assert parse_command("drop cost") == DropCommand(variables=("cost",))
  assert parse_command("drop if sex == 'F'") == DropCommand(
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
  )
  assert parse_command("select age sex") == SelectCommand(("age", "sex"))
  assert parse_command("rename sex gender") == RenameCommand("sex", "gender")


def test_parse_phase_3_generate_and_replace_commands() -> None:
  assert parse_command("generate log_cost = log(cost)") == GenerateCommand(
    variable="log_cost",
    expression=FunctionCallExpression(
      name="log",
      arguments=(IdentifierExpression("cost"),),
    ),
  )
  assert parse_command("replace cost = cost * 2 if sex == 'F'") == ReplaceCommand(
    variable="cost",
    expression=BinaryExpression(
      left=IdentifierExpression("cost"),
      operator="*",
      right=NumberExpression(2),
    ),
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
  )


def test_parse_phase_3_grouping_commands() -> None:
  assert parse_command("tabulate sex") == TabulateCommand(("sex",))
  assert parse_command("tabulate sex age, row col missing") == TabulateCommand(
    variables=("sex", "age"),
    row_percent=True,
    column_percent=True,
    include_missing=True,
  )
  assert parse_command("collapse mean age cost, by(sex)") == CollapseCommand(
    statistic="mean",
    variables=("age", "cost"),
    groups=("sex",),
  )
  assert parse_command("by sex: summarize age cost") == ByCommand(
    groups=("sex",),
    command=SummarizeCommand(("age", "cost")),
  )
  assert parse_command("by sex age: count") == ByCommand(
    groups=("sex", "age"),
    command=CountCommand(),
  )


def test_parse_phase_4_sql_commands() -> None:
  assert parse_command("use summary") == UseCommand(Path("summary"))
  assert parse_command(
    "sql select sex, avg(bmi) as mean_bmi from active group by sex"
  ) == SqlCommand(query="select sex, avg(bmi) as mean_bmi from active group by sex")
  assert parse_command(
    "sql select sex, avg(bmi) from active group by sex into summary"
  ) == SqlCommand(
    query="select sex, avg(bmi) from active group by sex",
    into="summary",
  )
  assert parse_command("sql select * from active   into summary") == SqlCommand(
    query="select * from active",
    into="summary",
  )
  assert parse_command('sql """\nselect sex, count(*) as n\nfrom active\n"""') == SqlCommand(
    query="select sex, count(*) as n\nfrom active"
  )
  assert parse_command(
    'sql """\nselect sex, count(*) as n\nfrom active\n""" into grouped'
  ) == SqlCommand(
    query="select sex, count(*) as n\nfrom active",
    into="grouped",
  )


def test_parse_phase_8_run_command() -> None:
  assert parse_command("run analysis.td") == RunCommand(Path("analysis.td"))


def test_parse_phase_9_configuration_and_persistence_commands() -> None:
  assert parse_command("set graph_format png") == SetCommand("graph_format", "png")
  assert parse_command("set artifact_dir artifacts/custom") == SetCommand(
    "artifact_dir",
    "artifacts/custom",
  )
  assert parse_command('set artifact_dir "my plots"') == SetCommand(
    "artifact_dir",
    "my plots",
  )
  assert parse_command("set graph_open off") == SetCommand("graph_open", "off")
  assert parse_command("save output.parquet") == SaveCommand(Path("output.parquet"))
  assert parse_command("export output.parquet, replace") == ExportCommand(
    Path("output.parquet"),
    replace=True,
  )


def test_parse_phase_6_visualization_commands() -> None:
  assert parse_command("histogram age") == HistogramCommand(variable="age")
  assert parse_command("histogram age, bins=20 saving(figures/age.svg) noopen") == (
    HistogramCommand(
      variable="age",
      bins=20,
      saving=Path("figures/age.svg"),
      open_artifact=False,
    )
  )
  assert parse_command("scatter bmi age") == ScatterCommand(
    y_variable="bmi",
    x_variable="age",
  )
  assert parse_command("scatter bmi age, saving(artifacts/bmi-age.png)") == ScatterCommand(
    y_variable="bmi",
    x_variable="age",
    saving=Path("artifacts/bmi-age.png"),
  )
  assert parse_command("bar sex, missing noopen") == BarCommand(
    variable="sex",
    include_missing=True,
    open_artifact=False,
  )


def test_parse_expression_with_precedence_and_function_call() -> None:
  assert parse_expression("sqrt(age + 1) >= 5") == BinaryExpression(
    left=FunctionCallExpression(
      name="sqrt",
      arguments=(
        BinaryExpression(
          left=IdentifierExpression("age"),
          operator="+",
          right=NumberExpression(1),
        ),
      ),
    ),
    operator=">=",
    right=NumberExpression(5),
  )


def test_parse_exit_aliases() -> None:
  assert parse_command("exit") == ExitCommand()
  assert parse_command("quit") == ExitCommand()


@pytest.mark.parametrize(
  "text",
  [
    "",
    "use",
    "use one.parquet two.parquet",
    "use data.parquet,",
    "use data.parquet, eager",
    "use data.parquet, lazy=true",
    "use data.parquet, lazy lazy",
    "use data.parquet, engine=duckdb",
    "use data.parquet, lazy engine=spark",
    "join",
    "join lookup",
    "join lookup id",
    "join lookup on",
    "join lookup on id id",
    "join lookup on id, how=right",
    "join lookup on id, suffix()",
    "join lookup on id, suffix(_x) suffix(_y)",
    "join lookup on id, replace",
    "join active on id",
    "join bad-name on id",
    "append",
    "append followup extra",
    "append followup, replace",
    "append followup if age > 18",
    "append active",
    "append bad-name",
    "reshape",
    "reshape wider income, i(id) j(year)",
    "reshape long, i(id) j(year)",
    "reshape long income if age > 18, i(id) j(year)",
    "reshape long income = cost, i(id) j(year)",
    "reshape long income, i(id)",
    "reshape long income, j(year)",
    "reshape long income, i() j(year)",
    "reshape long income, i(id) j(year month)",
    "reshape long income income, i(id) j(year)",
    "reshape long income, i(id id) j(year)",
    "reshape long income, i(id) j(income)",
    "reshape long income, i(income) j(year)",
    "reshape long income, i(id) j(year), extra",
    "reshape long income, i(id) j(year) replace",
    "panel firm_id year extra",
    "panel firm_id if year > 2020",
    "panel firm_id year, replace",
    "panel firm_id = year",
    "panel firm_id firm_id",
    "panel clear now",
    "describe age",
    "describe if age > 18",
    "exit now",
    "unknown",
    "summarize age = 5",
    "summarize age if",
    "summarize age if age >=",
    "summarize age if if age > 18",
    "summarize age if age > 18 if bmi > 20",
    "summarize age,",
    "summarize age, limit=",
    "summarize age, limit 10",
    "codebook age if age > 18",
    "codebook age, detail",
    "count age",
    "count if age > 18",
    "head 1 2",
    "head -1",
    "head 1.5",
    "head five",
    "head, limit=10",
    "tail 1 2",
    "tail -1",
    "tail 1.5",
    "tail five",
    "tail if age > 18",
    "keep",
    "keep age if age > 18",
    "drop",
    "drop age = 1",
    "select",
    "select age if age > 18",
    "rename age",
    "rename age years now",
    "generate new",
    "generate new = age if age > 18",
    "replace cost",
    "replace cost = cost * 2, force",
    "tabulate",
    "tabulate age bmi sex",
    "tabulate age, row",
    "tabulate age bmi, exact",
    "collapse median age, by(sex)",
    "collapse mean age",
    "collapse mean age, by()",
    "by: summarize age",
    "by sex:",
    "by sex: by age: count",
    "sql",
    'sql """select * from active',
    "sql select * from active into",
    "sql select * from active into active",
    "sql select * from active into __tabdat_next",
    "sql select * from active into bad-name",
    "histogram",
    "histogram age bmi",
    "histogram age if age > 18",
    "histogram age, width=200",
    "histogram age, bins=0",
    "histogram age, bins",
    "histogram age, bins=ten",
    "histogram age, noopen=false",
    "scatter bmi",
    "scatter bmi age cost",
    "scatter bmi age, bins=20",
    "scatter bmi age, noopen=true",
    "bar",
    "bar sex age",
    "bar sex, bins=20",
    "bar sex, missing=true",
    "run",
    "run first.td second.td",
    "set",
    "set graph_format",
    "set unknown on",
    "save",
    "save out.parquet, force",
    "save out.parquet, replace=true",
    "export",
    'summarize age if sex == "F',
    "summarize age if age $ 18",
  ],
)
def test_parse_invalid_commands(text: str) -> None:
  with pytest.raises(ParseError):
    parse_command(text)

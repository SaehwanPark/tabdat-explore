"""Command parser for the early TabDat command language."""

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NoReturn, cast

from tabdat.errors import ParseError
from tabdat.models import (
  AppendCommand,
  BarCommand,
  BinaryExpression,
  ByCommand,
  CfRegressCommand,
  CodebookCommand,
  CollapseCommand,
  Command,
  CommandOption,
  CountCommand,
  DescribeCommand,
  DropCommand,
  EstatCommand,
  ExitCommand,
  ExportCommand,
  Expression,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HistogramCommand,
  IdentifierExpression,
  IvRegressCommand,
  JoinCommand,
  KeepCommand,
  NumberExpression,
  PanelCommand,
  ParsedCommand,
  PredictCommand,
  RegressCommand,
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
  UnaryExpression,
  UseCommand,
  XtDataCommand,
  XtRegCommand,
)
from tabdat.monads import Err, Ok, Result, result, result_either

_EXECUTABLE_COMMANDS = {
  "use",
  "describe",
  "summarize",
  "codebook",
  "count",
  "head",
  "tail",
  "keep",
  "drop",
  "select",
  "rename",
  "generate",
  "replace",
  "tabulate",
  "collapse",
  "join",
  "append",
  "reshape",
  "panel",
  "sql",
  "histogram",
  "scatter",
  "bar",
  "run",
  "set",
  "save",
  "export",
  "regress",
  "predict",
  "estat",
  "ivregress",
  "xtreg",
  "xtdata",
  "cfregress",
  "exit",
  "quit",
}
_PARSED_ONLY_COMMANDS: set[str] = set()
_COLLAPSE_STATS = {"count", "mean", "sum", "min", "max"}
_BINARY_PRECEDENCE = {
  "==": 1,
  "!=": 1,
  "<": 1,
  "<=": 1,
  ">": 1,
  ">=": 1,
  "+": 2,
  "-": 2,
  "*": 3,
  "/": 3,
}


@dataclass(frozen=True)
class _Token:
  kind: Literal["identifier", "number", "string", "symbol"]
  text: str
  start: int
  end: int


@dataclass(frozen=True)
class _CommandParts:
  name: str
  arguments: tuple[str, ...]
  condition: Expression | None
  options: tuple[CommandOption, ...]
  expression: Expression | None = None


def parse_command(text: str) -> Command:
  stripped = text.strip()
  if not stripped:
    raise ParseError("empty command")

  command_name = stripped.split(maxsplit=1)[0].lower()

  if command_name == "use":
    return _parse_use(stripped)
  if command_name == "by":
    return _parse_by(stripped)
  if command_name == "sql":
    return _parse_sql(stripped)
  if command_name == "run":
    return _parse_run(stripped)

  return _parse_structured_command(stripped)


def _parse_structured_command(text: str) -> Command:
  command = _parse_structured_command_result(text)
  return result_either(command, _raise_parse_error, lambda parsed: parsed)


@result.block
def _parse_structured_command_result(
  text: str,
) -> Generator[Result[Any, str], Any, Command]:
  tokens = yield _tokenize_result(text)
  parts = yield _parse_command_parts_result(tokens)
  command = yield _build_command_from_parts_result(parts)
  return cast(Command, command)


def _parse_command_parts_result(tokens: tuple[_Token, ...]) -> Result[_CommandParts, str]:
  try:
    return Ok(_parse_command_parts(tokens))
  except ParseError as exc:
    return Err(str(exc))


def _build_command_from_parts_result(parts: _CommandParts) -> Result[Command, str]:
  try:
    return Ok(_build_command_from_parts(parts))
  except ParseError as exc:
    return Err(str(exc))


def _tokenize_result(text: str) -> Result[tuple[_Token, ...], str]:
  try:
    return Ok(_tokenize(text))
  except ParseError as exc:
    return Err(str(exc))


def _raise_parse_error(message: str) -> NoReturn:
  raise ParseError(message)


def _build_command_from_parts(parts: _CommandParts) -> Command:
  if parts.name == "describe":
    if parts.arguments or parts.condition is not None or parts.options:
      raise ParseError("describe does not accept arguments, if clauses, or options")
    return DescribeCommand()

  if parts.name == "summarize":
    if parts.expression is not None:
      raise ParseError("summarize does not accept assignment syntax")
    if parts.condition is None and not parts.options:
      return SummarizeCommand(variables=parts.arguments)
    return ParsedCommand(
      name=parts.name,
      arguments=parts.arguments,
      condition=parts.condition,
      options=parts.options,
    )

  if parts.name == "codebook":
    if parts.expression is not None:
      raise ParseError("codebook does not accept assignment syntax")
    if parts.condition is not None or parts.options:
      raise ParseError("codebook does not accept if clauses or options")
    return CodebookCommand(variables=parts.arguments)

  if parts.name == "count":
    has_unsupported_parts = (
      parts.arguments
      or parts.condition is not None
      or parts.options
      or parts.expression is not None
    )
    if has_unsupported_parts:
      raise ParseError("count does not accept arguments, if clauses, options, or assignment syntax")
    return CountCommand()

  if parts.name == "head":
    return HeadCommand(limit=_parse_preview_limit(parts, "head"))

  if parts.name == "tail":
    return TailCommand(limit=_parse_preview_limit(parts, "tail"))

  if parts.name == "keep":
    return _parse_keep_or_drop(parts, "keep")

  if parts.name == "drop":
    return _parse_keep_or_drop(parts, "drop")

  if parts.name == "select":
    if parts.condition is not None or parts.options or parts.expression is not None:
      raise ParseError("select only accepts a variable list")
    if not parts.arguments:
      raise ParseError("select expects at least one variable")
    return SelectCommand(variables=parts.arguments)

  if parts.name == "rename":
    if parts.condition is not None or parts.options or parts.expression is not None:
      raise ParseError("rename expects exactly two variables: rename old new")
    if len(parts.arguments) != 2:
      raise ParseError("rename expects exactly two variables: rename old new")
    return RenameCommand(old_name=parts.arguments[0], new_name=parts.arguments[1])

  if parts.name == "generate":
    if parts.condition is not None or parts.options:
      raise ParseError("generate does not accept if clauses or options")
    if len(parts.arguments) != 1 or parts.expression is None:
      raise ParseError("generate expects syntax: generate new = expression")
    return GenerateCommand(variable=parts.arguments[0], expression=parts.expression)

  if parts.name == "replace":
    if parts.options:
      raise ParseError("replace does not accept options")
    if len(parts.arguments) != 1 or parts.expression is None:
      raise ParseError("replace expects syntax: replace existing = expression")
    return ReplaceCommand(
      variable=parts.arguments[0],
      expression=parts.expression,
      condition=parts.condition,
    )

  if parts.name == "tabulate":
    return _parse_tabulate(parts)

  if parts.name == "collapse":
    return _parse_collapse(parts)

  if parts.name == "join":
    return _parse_join(parts)

  if parts.name == "append":
    return _parse_append(parts)

  if parts.name == "reshape":
    return _parse_reshape(parts)

  if parts.name == "panel":
    return _parse_panel(parts)

  if parts.name == "histogram":
    return _parse_histogram(parts)

  if parts.name == "scatter":
    return _parse_scatter(parts)

  if parts.name == "bar":
    return _parse_bar(parts)

  if parts.name == "set":
    return _parse_set(parts)

  if parts.name == "save":
    return _parse_save_or_export(parts, "save")

  if parts.name == "export":
    return _parse_save_or_export(parts, "export")

  if parts.name == "regress":
    return _parse_regress(parts)

  if parts.name == "predict":
    return _parse_predict(parts)

  if parts.name == "estat":
    return _parse_estat(parts)

  if parts.name == "ivregress":
    return _parse_ivregress(parts)

  if parts.name == "xtreg":
    return _parse_xtreg(parts)

  if parts.name == "xtdata":
    return _parse_xtdata(parts)

  if parts.name == "cfregress":
    return _parse_cfregress(parts)

  if parts.name in {"exit", "quit"}:
    if parts.arguments or parts.condition is not None or parts.options:
      raise ParseError(f"{parts.name} does not accept arguments, if clauses, or options")
    return ExitCommand()

  if parts.name in _PARSED_ONLY_COMMANDS:
    return ParsedCommand(
      name=parts.name,
      arguments=parts.arguments,
      condition=parts.condition,
      options=parts.options,
      expression=parts.expression,
    )

  raise ParseError(f"unknown command: {parts.name}")


def parse_expression(text: str) -> Expression:
  tokens = _tokenize(text)
  if not tokens:
    raise ParseError("missing expression")
  parser = _ExpressionParser(tokens)
  expression = parser.parse()
  if not parser.at_end:
    raise ParseError(f"unsupported token in expression: {parser.peek.text}")
  return expression


def _parse_use(text: str) -> UseCommand:
  body = text[3:].strip()
  if not body:
    raise ParseError("use expects exactly one path: use <path>")

  path_text, separator, option_text = body.partition(",")
  path_parts = path_text.split()
  if len(path_parts) != 1:
    raise ParseError("use expects exactly one path: use <path>")

  if not separator:
    return UseCommand(path=_parse_use_path(path_parts[0]))

  options = _parse_use_options(option_text)
  is_lazy = "lazy" in options
  engine = options.get("engine")
  if engine is not None and engine not in {"duckdb", "polars"}:
    raise ParseError("use engine must be duckdb or polars")
  if engine is not None and not is_lazy:
    raise ParseError("use engine option requires lazy mode")
  lazy_engine = cast(Literal["duckdb", "polars"] | None, engine)
  return UseCommand(
    path=_parse_use_path(path_parts[0]),
    execution_mode="lazy" if is_lazy else "eager",
    lazy_engine=lazy_engine or ("duckdb" if is_lazy else None),
  )


def _parse_use_path(path_text: str) -> Path | str:
  if _is_remote_uri(path_text):
    return path_text
  return Path(path_text)


def _is_remote_uri(path_text: str) -> bool:
  return "://" in path_text


def _parse_use_options(option_text: str) -> dict[str, str | bool]:
  if not option_text.strip():
    raise ParseError("use options cannot be empty")

  parsed: dict[str, str | bool] = {}
  for raw_option in option_text.split():
    name, separator, value = raw_option.partition("=")
    normalized = name.lower()
    if not normalized:
      raise ParseError("use options cannot be empty")
    if normalized in parsed:
      raise ParseError(f"use option specified more than once: {normalized}")
    if normalized == "lazy":
      if separator:
        raise ParseError("use lazy option does not accept a value")
      parsed[normalized] = True
      continue
    if normalized == "engine":
      if not separator or not value:
        raise ParseError("use engine option expects a value")
      parsed[normalized] = value.lower()
      continue
    raise ParseError(f"unknown use option: {normalized}")
  return parsed


def _parse_by(text: str) -> ByCommand:
  before, separator, after = text.partition(":")
  if not separator:
    raise ParseError("by expects syntax: by group_vars: command")
  groups = tuple(before.split()[1:])
  if not groups:
    raise ParseError("by expects at least one grouping variable")
  if not after.strip():
    raise ParseError("by expects a command after :")
  command = parse_command(after.strip())
  if isinstance(command, ByCommand):
    raise ParseError("nested by commands are not supported")
  return ByCommand(groups=groups, command=command)


def _parse_sql(text: str) -> SqlCommand:
  body = text[3:].strip()
  if not body:
    raise ParseError("sql expects a query")

  if body.startswith('"""'):
    query, remainder = _parse_triple_quoted_sql(body)
  else:
    query, remainder = _split_sql_into(body)

  normalized_query = query.strip()
  if not normalized_query:
    raise ParseError("sql expects a query")

  into = _parse_sql_into_remainder(remainder)
  if into is not None:
    _validate_sql_table_name(into)
  return SqlCommand(query=normalized_query, into=into)


def _parse_triple_quoted_sql(body: str) -> tuple[str, str]:
  closing_index = body.find('"""', 3)
  if closing_index == -1:
    raise ParseError('sql multiline query is missing closing """')
  query = body[3:closing_index]
  remainder = body[closing_index + 3 :].strip()
  return query, remainder


def _split_sql_into(body: str) -> tuple[str, str]:
  stripped_body = body.rstrip()
  parts = stripped_body.rsplit(maxsplit=2)
  if parts and parts[-1].lower() == "into":
    raise ParseError("sql into expects syntax: sql <query> into <table>")
  if len(parts) >= 3 and parts[-2].lower() == "into":
    into_start = stripped_body.rfind(parts[-2])
    query = stripped_body[:into_start].rstrip()
    return query, f"into {parts[-1]}"
  return body, ""


def _parse_sql_into_remainder(remainder: str) -> str | None:
  if not remainder:
    return None
  parts = remainder.split()
  if len(parts) != 2 or parts[0].lower() != "into":
    raise ParseError("sql into expects syntax: sql <query> into <table>")
  return parts[1]


def _validate_sql_table_name(table_name: str) -> None:
  if not table_name.isidentifier():
    raise ParseError("sql into table name must be an identifier")
  normalized = table_name.lower()
  if normalized == "active" or normalized.startswith("__tabdat_"):
    raise ParseError(f"sql into cannot use reserved table name: {table_name}")


def _require_unique(command_name: str, values: tuple[str, ...]) -> None:
  if len(set(values)) != len(values):
    raise ParseError(f"{command_name} variable list contains duplicates")


def _parse_run(text: str) -> RunCommand:
  body = text[3:].strip()
  if not body:
    raise ParseError("run expects exactly one path: run <script>")
  path_parts = body.split()
  if len(path_parts) != 1:
    raise ParseError("run expects exactly one path: run <script>")
  return RunCommand(path=Path(path_parts[0]))


def _parse_set(parts: _CommandParts) -> SetCommand:
  if parts.condition is not None or parts.options or parts.expression is not None:
    raise ParseError("set expects syntax: set name value")
  if len(parts.arguments) != 2:
    raise ParseError("set expects syntax: set name value")
  name = parts.arguments[0].lower()
  if name not in {"graph_format", "artifact_dir", "graph_open"}:
    raise ParseError(f"unknown setting: {parts.arguments[0]}")
  return SetCommand(
    name=cast(Literal["graph_format", "artifact_dir", "graph_open"], name),
    value=parts.arguments[1],
  )


def _parse_keep_or_drop(parts: _CommandParts, command_name: str) -> KeepCommand | DropCommand:
  if parts.options or parts.expression is not None:
    raise ParseError(f"{command_name} does not accept options or assignment syntax")
  if parts.condition is not None and parts.arguments:
    raise ParseError(f"{command_name} cannot combine a variable list with an if clause")
  if parts.condition is None and not parts.arguments:
    raise ParseError(f"{command_name} expects a variable list or if clause")
  if command_name == "keep":
    return KeepCommand(variables=parts.arguments, condition=parts.condition)
  return DropCommand(variables=parts.arguments, condition=parts.condition)


def _parse_tabulate(parts: _CommandParts) -> TabulateCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("tabulate does not accept if clauses or assignment syntax")
  if len(parts.arguments) not in {1, 2}:
    raise ParseError("tabulate expects one or two variables")

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"row", "col", "missing"}
  if unsupported:
    raise ParseError(f"tabulate unsupported option: {', '.join(sorted(unsupported))}")
  for option in parts.options:
    if option.value is not True:
      raise ParseError(f"tabulate option {option.name} does not accept a value")

  if len(parts.arguments) == 1 and option_names & {"row", "col"}:
    raise ParseError("one-way tabulate does not accept row or col options")

  return TabulateCommand(
    variables=parts.arguments,
    row_percent="row" in option_names,
    column_percent="col" in option_names,
    include_missing="missing" in option_names,
  )


def _parse_collapse(parts: _CommandParts) -> CollapseCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("collapse does not accept if clauses or assignment syntax")
  if len(parts.arguments) < 2:
    raise ParseError("collapse expects syntax: collapse stat varlist, by(group_vars)")

  statistic = parts.arguments[0].lower()
  if statistic not in _COLLAPSE_STATS:
    raise ParseError(f"collapse unsupported statistic: {parts.arguments[0]}")
  statistic_literal = cast(Literal["count", "mean", "sum", "min", "max"], statistic)

  by_options = tuple(option for option in parts.options if option.name == "by")
  if len(by_options) != 1 or len(parts.options) != 1:
    raise ParseError("collapse expects exactly one by(group_vars) option")
  groups = by_options[0].value
  if not isinstance(groups, tuple) or not groups:
    raise ParseError("collapse by() expects at least one grouping variable")

  return CollapseCommand(
    statistic=statistic_literal,
    variables=parts.arguments[1:],
    groups=groups,
  )


def _parse_join(parts: _CommandParts) -> JoinCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("join expects syntax: join <table> on <keylist>")
  if len(parts.arguments) < 3:
    raise ParseError("join expects syntax: join <table> on <keylist>")
  table_name = parts.arguments[0]
  if parts.arguments[1].lower() != "on":
    raise ParseError("join expects syntax: join <table> on <keylist>")
  keys = parts.arguments[2:]
  if len(set(keys)) != len(keys):
    raise ParseError("join key list contains duplicates")
  _validate_sql_table_name(table_name)

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"how", "suffix"}
  if unsupported:
    raise ParseError(f"join unsupported option: {', '.join(sorted(unsupported))}")
  how = _single_text_option(parts.options, "how", "join") or "inner"
  if how not in {"inner", "left"}:
    raise ParseError("join how must be inner or left")
  suffix = _single_text_option(parts.options, "suffix", "join") or "_right"
  if not suffix:
    raise ParseError("join suffix cannot be empty")
  return JoinCommand(
    table_name=table_name,
    keys=keys,
    how=cast(Literal["inner", "left"], how),
    suffix=suffix,
  )


def _parse_append(parts: _CommandParts) -> AppendCommand:
  if parts.condition is not None or parts.options or parts.expression is not None:
    raise ParseError("append expects syntax: append <table>")
  if len(parts.arguments) != 1:
    raise ParseError("append expects syntax: append <table>")
  table_name = parts.arguments[0]
  _validate_sql_table_name(table_name)
  return AppendCommand(table_name=table_name)


def _parse_reshape(parts: _CommandParts) -> ReshapeCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("reshape expects syntax: reshape long|wide varlist, i(id_vars) j(name)")
  if len(parts.arguments) < 2:
    raise ParseError("reshape expects syntax: reshape long|wide varlist, i(id_vars) j(name)")

  direction = parts.arguments[0].lower()
  if direction not in {"long", "wide"}:
    raise ParseError("reshape direction must be long or wide")
  variables = parts.arguments[1:]
  _require_unique("reshape", variables)

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"i", "j"}
  if unsupported:
    raise ParseError(f"reshape unsupported option: {', '.join(sorted(unsupported))}")

  identifiers = _single_tuple_option(parts.options, "i", "reshape")
  if identifiers is None or not identifiers:
    raise ParseError("reshape expects exactly one i(id_vars) option")
  _require_unique("reshape", identifiers)

  j_values = _single_tuple_option(parts.options, "j", "reshape")
  if j_values is None or len(j_values) != 1:
    raise ParseError("reshape expects exactly one j(name) option")
  j_variable = j_values[0]

  overlaps = set(variables) & set(identifiers)
  if overlaps or j_variable in variables or j_variable in identifiers:
    raise ParseError("reshape variables, i(), and j() names must be distinct")

  return ReshapeCommand(
    direction=cast(Literal["long", "wide"], direction),
    variables=variables,
    identifiers=identifiers,
    j_variable=j_variable,
  )


def _parse_panel(parts: _CommandParts) -> PanelCommand:
  if parts.condition is not None or parts.options or parts.expression is not None:
    raise ParseError("panel expects syntax: panel [<id_var> <time_var>|clear]")
  if not parts.arguments:
    return PanelCommand(action="report")
  if parts.arguments[0] == "clear":
    if parts.arguments == ("clear",):
      return PanelCommand(action="clear")
    raise ParseError("panel expects syntax: panel [<id_var> <time_var>|clear]")
  if len(parts.arguments) != 2:
    raise ParseError("panel expects syntax: panel [<id_var> <time_var>|clear]")
  if parts.arguments[0] == parts.arguments[1]:
    raise ParseError("panel id and time variables must be distinct")
  return PanelCommand(
    action="set",
    id_variable=parts.arguments[0],
    time_variable=parts.arguments[1],
  )


def _parse_histogram(parts: _CommandParts) -> HistogramCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("histogram does not accept if clauses or assignment syntax")
  if len(parts.arguments) != 1:
    raise ParseError("histogram expects exactly one variable")

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"bins", "saving", "noopen"}
  if unsupported:
    raise ParseError(f"histogram unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "histogram", {"noopen"})

  return HistogramCommand(
    variable=parts.arguments[0],
    bins=_single_integer_option(parts.options, "bins", "histogram", minimum=1),
    saving=_single_path_option(parts.options, "saving", "histogram"),
    open_artifact="noopen" not in option_names,
  )


def _parse_scatter(parts: _CommandParts) -> ScatterCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("scatter does not accept if clauses or assignment syntax")
  if len(parts.arguments) != 2:
    raise ParseError("scatter expects syntax: scatter y_var x_var")

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"saving", "noopen"}
  if unsupported:
    raise ParseError(f"scatter unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "scatter", {"noopen"})

  return ScatterCommand(
    y_variable=parts.arguments[0],
    x_variable=parts.arguments[1],
    saving=_single_path_option(parts.options, "saving", "scatter"),
    open_artifact="noopen" not in option_names,
  )


def _parse_bar(parts: _CommandParts) -> BarCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("bar does not accept if clauses or assignment syntax")
  if len(parts.arguments) != 1:
    raise ParseError("bar expects exactly one variable")

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"saving", "missing", "noopen"}
  if unsupported:
    raise ParseError(f"bar unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "bar", {"missing", "noopen"})

  return BarCommand(
    variable=parts.arguments[0],
    saving=_single_path_option(parts.options, "saving", "bar"),
    include_missing="missing" in option_names,
    open_artifact="noopen" not in option_names,
  )


def _parse_save_or_export(parts: _CommandParts, command_name: str) -> SaveCommand | ExportCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(f"{command_name} does not accept if clauses or assignment syntax")
  if len(parts.arguments) != 1:
    raise ParseError(f"{command_name} expects exactly one path")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"replace"}
  if unsupported:
    raise ParseError(f"{command_name} unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, command_name, {"replace"})
  if command_name == "save":
    return SaveCommand(path=Path(parts.arguments[0]), replace="replace" in option_names)
  return ExportCommand(path=Path(parts.arguments[0]), replace="replace" in option_names)


def _parse_regress(parts: _CommandParts) -> RegressCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("regress expects syntax: regress <y> <xvars>")
  if len(parts.arguments) < 2:
    raise ParseError("regress expects syntax: regress <y> <xvars>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"robust", "cluster", "noconstant", "wls", "gls"}
  if unsupported:
    raise ParseError(f"regress unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "regress", {"robust", "noconstant"})
  cluster_values = _single_tuple_option(parts.options, "cluster", "regress")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("regress option cluster expects one variable")
  wls_values = _single_tuple_option(parts.options, "wls", "regress")
  if wls_values is not None and len(wls_values) != 1:
    raise ParseError("regress option wls expects one variable")
  gls_values = _single_tuple_option(parts.options, "gls", "regress")
  if gls_values is not None and len(gls_values) != 1:
    raise ParseError("regress option gls expects one variable")
  if wls_values is not None and gls_values is not None:
    raise ParseError("regress cannot combine wls and gls")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("regress cannot combine robust and cluster")
  estimator: Literal["ols", "wls", "gls"] = "ols"
  weight_variable: str | None = None
  if wls_values is not None:
    estimator = "wls"
    weight_variable = wls_values[0]
  if gls_values is not None:
    estimator = "gls"
    weight_variable = gls_values[0]
  outcome = parts.arguments[0]
  predictors = parts.arguments[1:]
  return RegressCommand(
    outcome=outcome,
    predictors=predictors,
    estimator=estimator,
    weight_variable=weight_variable,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_predict(parts: _CommandParts) -> PredictCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("predict expects syntax: predict <newvar>")
  if len(parts.arguments) != 1:
    raise ParseError("predict expects syntax: predict <newvar>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"xb", "residuals"}
  if unsupported:
    raise ParseError(f"predict unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "predict", {"xb", "residuals"})
  if "xb" in option_names and "residuals" in option_names:
    raise ParseError("predict options xb and residuals cannot be combined")
  return PredictCommand(
    target_variable=parts.arguments[0],
    kind="residuals" if "residuals" in option_names else "xb",
  )


def _parse_estat(parts: _CommandParts) -> EstatCommand:
  if parts.condition is not None or parts.options or parts.expression is not None:
    raise ParseError("estat expects syntax: estat <residuals|ovtest|vif|firststage|overid|hausman>")
  if len(parts.arguments) != 1:
    raise ParseError("estat expects syntax: estat <residuals|ovtest|vif|firststage|overid|hausman>")
  subcommand = parts.arguments[0].lower()
  if subcommand not in {"residuals", "ovtest", "vif", "firststage", "overid", "hausman"}:
    raise ParseError(
      "estat subcommand must be residuals, ovtest, vif, firststage, overid, or hausman"
    )
  return EstatCommand(
    subcommand=cast(
      Literal["residuals", "ovtest", "vif", "firststage", "overid", "hausman"],
      subcommand,
    )
  )


def _parse_ivregress(parts: _CommandParts) -> IvRegressCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(
      "ivregress expects syntax: ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)"
    )
  if len(parts.arguments) < 2:
    raise ParseError(
      "ivregress expects syntax: ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)"
    )
  estimator = parts.arguments[0].lower()
  if estimator != "2sls":
    raise ParseError("ivregress estimator must be 2sls")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"endog", "iv", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"ivregress unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "ivregress", {"robust", "noconstant"})
  endog_values = _single_tuple_option(parts.options, "endog", "ivregress")
  if endog_values is None or len(endog_values) != 1:
    raise ParseError("ivregress option endog expects one variable")
  instrument_values = _single_tuple_option(parts.options, "iv", "ivregress")
  if instrument_values is None:
    raise ParseError("ivregress option iv expects at least one variable")
  cluster_values = _single_tuple_option(parts.options, "cluster", "ivregress")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("ivregress option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("ivregress cannot combine robust and cluster")
  outcome = parts.arguments[1]
  exogenous = parts.arguments[2:]
  endogenous = endog_values[0]
  if endogenous in exogenous:
    raise ParseError("ivregress endog variable must not appear in exogenous variables")
  return IvRegressCommand(
    outcome=outcome,
    exogenous=exogenous,
    endogenous=endogenous,
    instruments=instrument_values,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
    estimator="2sls",
  )


def _parse_xtreg(parts: _CommandParts) -> XtRegCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("xtreg expects syntax: xtreg <y> <xvars>, fe|re")
  if len(parts.arguments) < 2:
    raise ParseError("xtreg expects syntax: xtreg <y> <xvars>, fe|re")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"fe", "re", "robust", "cluster"}
  if unsupported:
    raise ParseError(f"xtreg unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "xtreg", {"fe", "re", "robust"})
  cluster_values = _single_tuple_option(parts.options, "cluster", "xtreg")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("xtreg option cluster expects one variable")
  has_fe = "fe" in option_names
  has_re = "re" in option_names
  if has_fe == has_re:
    raise ParseError("xtreg requires exactly one of fe or re")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("xtreg cannot combine robust and cluster")
  estimator: Literal["fe", "re"] = "fe" if has_fe else "re"
  return XtRegCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    estimator=estimator,
    robust=robust,
    cluster_variable=cluster_variable,
  )


def _parse_xtdata(parts: _CommandParts) -> XtDataCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("xtdata expects syntax: xtdata <varlist>, within|between")
  if not parts.arguments:
    raise ParseError("xtdata expects syntax: xtdata <varlist>, within|between")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"within", "between"}
  if unsupported:
    raise ParseError(f"xtdata unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "xtdata", {"within", "between"})
  has_within = "within" in option_names
  has_between = "between" in option_names
  if has_within == has_between:
    raise ParseError("xtdata requires exactly one of within or between")
  transform: Literal["within", "between"] = "within" if has_within else "between"
  return XtDataCommand(variables=parts.arguments, transform=transform)


def _parse_cfregress(parts: _CommandParts) -> CfRegressCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("cfregress expects syntax: cfregress <y> [exog_vars], endog(<var>) iv(<vars>)")
  if len(parts.arguments) < 1:
    raise ParseError("cfregress expects syntax: cfregress <y> [exog_vars], endog(<var>) iv(<vars>)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"endog", "iv", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"cfregress unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "cfregress", {"robust", "noconstant"})
  endog_values = _single_tuple_option(parts.options, "endog", "cfregress")
  if endog_values is None or len(endog_values) != 1:
    raise ParseError("cfregress option endog expects one variable")
  instrument_values = _single_tuple_option(parts.options, "iv", "cfregress")
  if instrument_values is None:
    raise ParseError("cfregress option iv expects at least one variable")
  cluster_values = _single_tuple_option(parts.options, "cluster", "cfregress")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("cfregress option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("cfregress cannot combine robust and cluster")
  outcome = parts.arguments[0]
  exogenous = parts.arguments[1:]
  endogenous = endog_values[0]
  if endogenous in exogenous:
    raise ParseError("cfregress endog variable must not appear in exogenous variables")
  return CfRegressCommand(
    outcome=outcome,
    exogenous=exogenous,
    endogenous=endogenous,
    instruments=instrument_values,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _single_integer_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
  *,
  minimum: int,
) -> int | None:
  matched = [option for option in options if option.name == name]
  if not matched:
    return None
  if len(matched) > 1:
    raise ParseError(f"{command_name} option {name} may only be supplied once")
  value = matched[0].value
  if isinstance(value, bool) or not isinstance(value, int):
    raise ParseError(f"{command_name} option {name} expects an integer value")
  if value < minimum:
    raise ParseError(f"{command_name} option {name} must be at least {minimum}")
  return value


def _single_path_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
) -> Path | None:
  matched = [option for option in options if option.name == name]
  if not matched:
    return None
  if len(matched) > 1:
    raise ParseError(f"{command_name} option {name} may only be supplied once")
  value = matched[0].value
  if not isinstance(value, str):
    raise ParseError(f"{command_name} option {name} expects a path")
  return Path(value)


def _single_text_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
) -> str | None:
  matched = [option for option in options if option.name == name]
  if not matched:
    return None
  if len(matched) > 1:
    raise ParseError(f"{command_name} option {name} may only be supplied once")
  value = matched[0].value
  if isinstance(value, tuple):
    if len(value) != 1:
      raise ParseError(f"{command_name} option {name} expects one value")
    return value[0]
  if not isinstance(value, str):
    raise ParseError(f"{command_name} option {name} expects a value")
  return value


def _single_tuple_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
) -> tuple[str, ...] | None:
  matched = [option for option in options if option.name == name]
  if not matched:
    return None
  if len(matched) > 1:
    raise ParseError(f"{command_name} option {name} may only be supplied once")
  value = matched[0].value
  if not isinstance(value, tuple):
    raise ParseError(f"{command_name} option {name} expects variables")
  return value


def _require_flag_options(
  options: tuple[CommandOption, ...],
  command_name: str,
  flag_names: set[str],
) -> None:
  for option in options:
    if option.name in flag_names and option.value is not True:
      raise ParseError(f"{command_name} option {option.name} does not accept a value")


def _parse_preview_limit(parts: _CommandParts, command_name: str) -> int:
  if parts.condition is not None or parts.options or parts.expression is not None:
    raise ParseError(f"{command_name} does not accept if clauses, options, or assignment syntax")
  if len(parts.arguments) > 1:
    raise ParseError(f"{command_name} accepts at most one row limit")
  if not parts.arguments:
    return 5

  limit_text = parts.arguments[0]
  try:
    limit = int(limit_text)
  except ValueError as exc:
    raise ParseError(f"{command_name} row limit must be a non-negative integer") from exc
  if not limit_text.isascii() or not limit_text.isdigit():
    raise ParseError(f"{command_name} row limit must be a non-negative integer")
  return limit


def _parse_command_parts(tokens: tuple[_Token, ...]) -> _CommandParts:
  stream = _TokenStream(tokens)
  first = stream.consume()
  if first.kind != "identifier":
    raise ParseError("command must start with a command name")

  name = first.text.lower()
  if name not in _EXECUTABLE_COMMANDS and name not in _PARSED_ONLY_COMMANDS:
    raise ParseError(f"unknown command: {name}")

  arguments: list[str] = []
  condition: Expression | None = None
  options: tuple[CommandOption, ...] = ()
  expression: Expression | None = None

  while not stream.at_end:
    token = stream.peek
    if token.text == ",":
      options = _parse_options(stream.remaining_after_current())
      stream.advance_to_end()
      break
    if token.kind == "identifier" and token.text.lower() == "if":
      if condition is not None:
        raise ParseError("duplicate if clause")
      stream.consume()
      condition_tokens, option_tokens = _split_expression_and_options(stream.remaining())
      if not condition_tokens:
        raise ParseError("missing expression after if")
      condition = _ExpressionParser(condition_tokens).parse_all()
      options = _parse_options(option_tokens) if option_tokens else options
      stream.advance_to_end()
      break
    if token.text == "=":
      if not arguments:
        raise ParseError(f"{name} assignment requires a target before =")
      stream.consume()
      if name == "replace":
        expression_tokens, condition_tokens, option_tokens = _split_replace_expression(
          stream.remaining()
        )
        if condition_tokens:
          condition = _ExpressionParser(condition_tokens).parse_all()
      else:
        expression_tokens, option_tokens = _split_expression_and_options(stream.remaining())
      if not expression_tokens:
        raise ParseError(f"{name} assignment requires an expression after =")
      expression = _ExpressionParser(expression_tokens).parse_all()
      options = _parse_options(option_tokens) if option_tokens else options
      stream.advance_to_end()
      break
    arguments.append(_parse_argument(stream))

  return _CommandParts(
    name=name,
    arguments=tuple(arguments),
    condition=condition,
    options=options,
    expression=expression,
  )


def _parse_argument(stream: "_TokenStream") -> str:
  parts: list[str] = []
  previous: _Token | None = None
  while not stream.at_end:
    token = stream.peek
    if token.text in {",", "="}:
      break
    if token.kind == "identifier" and token.text.lower() == "if":
      break
    if previous is not None and token.start > previous.end:
      break
    previous = stream.consume()
    parts.append(previous.text)
  if not parts:
    raise ParseError(f"unsupported token in command: {stream.peek.text}")
  return "".join(parts)


def _split_expression_and_options(
  tokens: tuple[_Token, ...],
) -> tuple[tuple[_Token, ...], tuple[_Token, ...]]:
  depth = 0
  for index, token in enumerate(tokens):
    if token.text == "(":
      depth += 1
    elif token.text == ")":
      depth -= 1
    elif token.kind == "identifier" and token.text.lower() == "if" and depth == 0:
      raise ParseError("duplicate if clause")
    elif token.text == "," and depth == 0:
      return tokens[:index], tokens[index + 1 :]
  return tokens, ()


def _split_replace_expression(
  tokens: tuple[_Token, ...],
) -> tuple[tuple[_Token, ...], tuple[_Token, ...], tuple[_Token, ...]]:
  depth = 0
  for index, token in enumerate(tokens):
    if token.text == "(":
      depth += 1
    elif token.text == ")":
      depth -= 1
    elif token.kind == "identifier" and token.text.lower() == "if" and depth == 0:
      condition_tokens, option_tokens = _split_expression_and_options(tokens[index + 1 :])
      return tokens[:index], condition_tokens, option_tokens
    elif token.text == "," and depth == 0:
      return tokens[:index], (), tokens[index + 1 :]
  return tokens, (), ()


def _parse_options(tokens: tuple[_Token, ...]) -> tuple[CommandOption, ...]:
  if not tokens:
    raise ParseError("comma must be followed by at least one option")

  stream = _TokenStream(tokens)
  options: list[CommandOption] = []
  while not stream.at_end:
    name = stream.consume()
    if name.kind != "identifier":
      raise ParseError("option names must be identifiers")
    value: str | int | float | bool | tuple[str, ...] = True
    if not stream.at_end and stream.peek.text == "(":
      stream.consume()
      value_tokens: list[_Token] = []
      while not stream.at_end and stream.peek.text != ")":
        value_tokens.append(stream.consume())
      if stream.at_end:
        raise ParseError(f"option {name.text} is missing closing )")
      stream.consume()
      if not value_tokens:
        raise ParseError(f"option {name.text} expects at least one value")
      value = _parenthesized_option_value(name.text, tuple(value_tokens))
    if not stream.at_end and stream.peek.text == "=":
      stream.consume()
      if stream.at_end:
        raise ParseError(f"option {name.text} requires a value after =")
      value_token = stream.consume()
      if value_token.text in {",", "=", "(", ")"}:
        raise ParseError(f"option {name.text} has malformed value")
      value = _option_value(value_token)
    elif not stream.at_end and stream.peek.kind in {"number", "string"}:
      raise ParseError(f"option {name.text} value must use option=value syntax")
    options.append(CommandOption(name=name.text, value=value))
  return tuple(options)


def _option_value(token: _Token) -> str | int | float:
  if token.kind == "number":
    return _parse_number(token.text)
  return token.text


def _parenthesized_option_value(
  option_name: str,
  tokens: tuple[_Token, ...],
) -> str | tuple[str, ...]:
  if option_name == "saving":
    return "".join(token.text for token in tokens)

  values: list[str] = []
  for token in tokens:
    if token.kind != "identifier":
      raise ParseError(f"option {option_name} values must be identifiers")
    values.append(token.text)
  return tuple(values)


def _tokenize(text: str) -> tuple[_Token, ...]:
  tokens: list[_Token] = []
  index = 0
  while index < len(text):
    char = text[index]
    if char.isspace():
      index += 1
      continue
    if char.isalpha() or char == "_":
      start = index
      index += 1
      while index < len(text) and (text[index].isalnum() or text[index] == "_"):
        index += 1
      tokens.append(_Token("identifier", text[start:index], start, index))
      continue
    if char.isdigit() or (char == "." and index + 1 < len(text) and text[index + 1].isdigit()):
      start = index
      index += 1
      while index < len(text) and (text[index].isdigit() or text[index] == "."):
        index += 1
      number_text = text[start:index]
      if number_text.count(".") > 1:
        raise ParseError(f"malformed number: {number_text}")
      tokens.append(_Token("number", number_text, start, index))
      continue
    if char in {"'", '"'}:
      quote = char
      index += 1
      value: list[str] = []
      while index < len(text) and text[index] != quote:
        value.append(text[index])
        index += 1
      if index >= len(text):
        raise ParseError("unterminated quoted string")
      index += 1
      tokens.append(_Token("string", "".join(value), index - len(value) - 1, index))
      continue
    two_char = text[index : index + 2]
    if two_char in {"==", "!=", "<=", ">="}:
      tokens.append(_Token("symbol", two_char, index, index + 2))
      index += 2
      continue
    if char in {",", "=", "<", ">", "+", "-", "*", "/", "(", ")", ":", "."}:
      tokens.append(_Token("symbol", char, index, index + 1))
      index += 1
      continue
    raise ParseError(f"unsupported token in command: {char}")
  return tuple(tokens)


def _parse_number(text: str) -> int | float:
  if "." in text:
    return float(text)
  return int(text)


class _ExpressionParser:
  def __init__(self, tokens: tuple[_Token, ...]) -> None:
    self._stream = _TokenStream(tokens)

  @property
  def at_end(self) -> bool:
    return self._stream.at_end

  @property
  def peek(self) -> _Token:
    return self._stream.peek

  def parse(self) -> Expression:
    return self._parse_binary(min_precedence=1)

  def parse_all(self) -> Expression:
    expression = self.parse()
    if not self._stream.at_end:
      raise ParseError(f"unsupported token in expression: {self._stream.peek.text}")
    return expression

  def _parse_binary(self, min_precedence: int) -> Expression:
    left = self._parse_primary()
    while not self._stream.at_end:
      operator = self._stream.peek.text
      precedence = _BINARY_PRECEDENCE.get(operator)
      if precedence is None or precedence < min_precedence:
        break
      self._stream.consume()
      if self._stream.at_end:
        raise ParseError(f"incomplete expression after {operator}")
      right = self._parse_binary(precedence + 1)
      operator_literal = cast(
        Literal["+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">="],
        operator,
      )
      left = BinaryExpression(left=left, operator=operator_literal, right=right)
    return left

  def _parse_primary(self) -> Expression:
    if self._stream.at_end:
      raise ParseError("missing expression")

    token = self._stream.consume()
    if token.kind == "identifier":
      if not self._stream.at_end and self._stream.peek.text == "(":
        return self._parse_function_call(token.text)
      return IdentifierExpression(token.text)
    if token.kind == "number":
      return NumberExpression(_parse_number(token.text))
    if token.kind == "string":
      return StringExpression(token.text)
    if token.text == "-":
      operand = self._parse_primary()
      return UnaryExpression(operator="-", operand=operand)
    if token.text == "(":
      expression = self._parse_binary(min_precedence=1)
      if self._stream.at_end or self._stream.consume().text != ")":
        raise ParseError("missing closing ) in expression")
      return expression
    raise ParseError(f"unsupported token in expression: {token.text}")

  def _parse_function_call(self, name: str) -> FunctionCallExpression:
    self._stream.consume()
    arguments: list[Expression] = []
    if not self._stream.at_end and self._stream.peek.text == ")":
      self._stream.consume()
      return FunctionCallExpression(name=name, arguments=())

    while True:
      arguments.append(self._parse_binary(min_precedence=1))
      if self._stream.at_end:
        raise ParseError(f"missing closing ) in function call: {name}")
      separator = self._stream.consume()
      if separator.text == ")":
        break
      if separator.text != ",":
        raise ParseError(f"function call {name} arguments must be separated by commas")
    return FunctionCallExpression(name=name, arguments=tuple(arguments))


class _TokenStream:
  def __init__(self, tokens: tuple[_Token, ...]) -> None:
    self._tokens = tokens
    self._position = 0

  @property
  def at_end(self) -> bool:
    return self._position >= len(self._tokens)

  @property
  def peek(self) -> _Token:
    if self.at_end:
      raise ParseError("unexpected end of command")
    return self._tokens[self._position]

  def consume(self) -> _Token:
    token = self.peek
    self._position += 1
    return token

  def remaining(self) -> tuple[_Token, ...]:
    return self._tokens[self._position :]

  def remaining_after_current(self) -> tuple[_Token, ...]:
    return self._tokens[self._position + 1 :]

  def advance_to_end(self) -> None:
    self._position = len(self._tokens)

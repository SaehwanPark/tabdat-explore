"""Command parser for the early TabDat command language."""

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NoReturn, cast

from tabdat.errors import ParseError
from tabdat.models import (
  AppendCommand,
  BarCommand,
  BayesCommand,
  BayesPlotCommand,
  BayesPrefixCommand,
  BinaryExpression,
  ByCommand,
  CfRegressCommand,
  CodebookCommand,
  CollapseCommand,
  Command,
  CommandOption,
  CountCommand,
  CvelasticnetCommand,
  CvlassoCommand,
  CvridgeCommand,
  DescribeCommand,
  DidCommand,
  DmlCommand,
  DrDidCommand,
  DropCommand,
  ElasticnetCommand,
  EstatCommand,
  ExitCommand,
  ExportCommand,
  Expression,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HeckmanCommand,
  HelpCommand,
  HistogramCommand,
  IdentifierExpression,
  IvRegressCommand,
  JoinCommand,
  KeepCommand,
  LassoCommand,
  LincomCommand,
  LogitCommand,
  LowessCommand,
  NbregCommand,
  NlCommand,
  NumberExpression,
  PanelCommand,
  ParsedCommand,
  PoissonCommand,
  PostlassoCommand,
  PredictCommand,
  ProbitCommand,
  QregCommand,
  RecodeCommand,
  RecodeRange,
  RecodeRule,
  RegressCommand,
  RenameCommand,
  ReplaceCommand,
  ReshapeCommand,
  RidgeCommand,
  RunCommand,
  SaveCommand,
  ScatterCommand,
  SelectCommand,
  SetCommand,
  SpregressCommand,
  SqlCommand,
  StregCommand,
  StringExpression,
  SummarizeCommand,
  TabulateCommand,
  TailCommand,
  TestCommand,
  TobitCommand,
  TtestCommand,
  UnaryExpression,
  UseCommand,
  XtAbondCommand,
  XtDataCommand,
  XtLogitCommand,
  XtRegCommand,
  ZinbCommand,
  ZipCommand,
)
from tabdat.monads import Err, Ok, Result, result, result_either

_EXECUTABLE_COMMANDS = {
  "use",
  "recode",
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
  "bayesplot",
  "run",
  "set",
  "save",
  "export",
  "regress",
  "lasso",
  "postlasso",
  "ridge",
  "elasticnet",
  "cvlasso",
  "cvridge",
  "cvelasticnet",
  "bayes",
  "qreg",
  "logit",
  "probit",
  "tobit",
  "heckman",
  "nl",
  "poisson",
  "nbreg",
  "zip",
  "zinb",
  "streg",
  "predict",
  "estat",
  "ivregress",
  "xtreg",
  "xtdata",
  "xtlogit",
  "xtabond",
  "lowess",
  "did",
  "drdid",
  "dml",
  "cfregress",
  "spregress",
  "test",
  "lincom",
  "ttest",
  "exit",
  "quit",
}
_PARSED_ONLY_COMMANDS: set[str] = set()
_COLLAPSE_STATS = {"count", "mean", "sum", "min", "max"}
_TABULATE_STATS = {"count", "mean", "sum", "min", "max"}
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
  command = _parse_command_result(text)
  return result_either(command, _raise_parse_error, lambda parsed: parsed)


def _parse_command_result(text: str) -> Result[Command, str]:
  stripped = text.strip()
  if not stripped:
    return Err("empty command")

  if stripped.startswith("?"):
    return _parse_help_result(stripped[1:].strip())

  command_name = stripped.split(maxsplit=1)[0].lower()

  if command_name == "help":
    return _parse_help_result(stripped[4:].strip())
  if command_name == "use":
    return _parse_use_result(stripped)
  if command_name == "recode":
    return _parse_recode_result(stripped)
  if command_name == "by":
    return _parse_by_result(stripped)
  if command_name == "test":
    return _parse_test_result(stripped)
  if command_name == "lincom":
    return _parse_lincom_result(stripped)
  if command_name == "ttest":
    return _parse_ttest_result(stripped)
  if (
    command_name == "bayes:"
    or command_name.startswith("bayes,")
    or (command_name == "bayes" and ":" in stripped)
  ):
    return _parse_bayes_prefix_result(stripped)
  if command_name == "sql":
    return _parse_sql_result(stripped)
  if command_name == "run":
    return _parse_run_result(stripped)

  return _parse_structured_command_result(stripped)


def _parse_help(body: str) -> HelpCommand:
  if not body:
    return HelpCommand()
  parts = body.split()
  if len(parts) != 1:
    raise ParseError("help expects at most one command name: help <command>")
  return HelpCommand(topic=parts[0].lower())


def _parse_help_result(body: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_help(body))
  except ParseError as exc:
    return Err(str(exc))


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


def _parse_use_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_use(text))
  except ParseError as exc:
    return Err(str(exc))


def _parse_test_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_test(text))
  except ParseError as exc:
    return Err(str(exc))


def _parse_recode_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_recode(text))
  except ParseError as exc:
    return Err(str(exc))


def _parse_lincom_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_lincom(text))
  except ParseError as exc:
    return Err(str(exc))


def _parse_ttest_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_ttest(text))
  except ParseError as exc:
    return Err(str(exc))


@result.block
def _parse_by_result(text: str) -> Generator[Result[Any, str], Any, Command]:
  before, separator, after = text.partition(":")
  if not separator:
    return cast(Command, (yield Err("by expects syntax: by group_vars: command")))
  groups = tuple(before.split()[1:])
  if not groups:
    return cast(Command, (yield Err("by expects at least one grouping variable")))
  if not after.strip():
    return cast(Command, (yield Err("by expects a command after :")))

  command = yield _parse_command_result(after.strip())
  if isinstance(command, ByCommand):
    return cast(Command, (yield Err("nested by commands are not supported")))
  if isinstance(command, HelpCommand):
    return cast(Command, (yield Err("help is not supported inside by commands")))
  return ByCommand(groups=groups, command=command)


@result.block
def _parse_bayes_prefix_result(text: str) -> Generator[Result[Any, str], Any, Command]:
  before, separator, after = text.partition(":")
  if not separator:
    return cast(Command, (yield Err("bayes prefix expects syntax: bayes [, options]: command")))

  before_stripped = before.strip()
  if before_stripped == "bayes":
    draws, burnin, chains, thin, seed = None, None, None, None, None
    priors: list[tuple[str, str]] = []
  else:
    if not before_stripped.startswith("bayes"):
      return cast(Command, (yield Err("invalid bayes prefix")))
    options_part = before_stripped[len("bayes") :].strip()
    if not options_part.startswith(","):
      return cast(Command, (yield Err("bayes prefix options must start with a comma")))

    tokens = yield _tokenize_result(options_part[1:].strip())
    try:
      parsed_options = _parse_options(tokens)
    except ParseError as exc:
      return cast(Command, (yield Err(str(exc))))

    draws, burnin, chains, thin, seed = None, None, None, None, None
    priors = []
    for option in parsed_options:
      if option.name == "draws":
        if not isinstance(option.value, (int, float)):
          return cast(Command, (yield Err("draws must be a numeric value")))
        draws = int(option.value)
      elif option.name in ("burnin", "tune"):
        if not isinstance(option.value, (int, float)):
          return cast(Command, (yield Err("burnin must be a numeric value")))
        burnin = int(option.value)
      elif option.name == "chains":
        if not isinstance(option.value, (int, float)):
          return cast(Command, (yield Err("chains must be a numeric value")))
        chains = int(option.value)
      elif option.name == "thin":
        if not isinstance(option.value, (int, float)):
          return cast(Command, (yield Err("thin must be a numeric value")))
        thin = int(option.value)
      elif option.name in ("seed", "rseed"):
        if not isinstance(option.value, (int, float)):
          return cast(Command, (yield Err("seed must be a numeric value")))
        seed = int(option.value)
      elif option.name == "prior":
        if not isinstance(option.value, tuple) or len(option.value) != 2:
          return cast(Command, (yield Err("prior expects (variable, distribution)")))
        priors.append((option.value[0], option.value[1]))
      else:
        return cast(Command, (yield Err(f"unsupported bayes option: {option.name}")))

  if not after.strip():
    return cast(Command, (yield Err("bayes expects a command after :")))

  inner_command = yield _parse_command_result(after.strip())
  if not isinstance(inner_command, (RegressCommand, LogitCommand)):
    return cast(Command, (yield Err("bayes prefix only supports regress and logit commands")))

  return BayesPrefixCommand(
    command=inner_command,
    draws=draws,
    burnin=burnin,
    chains=chains,
    thin=thin,
    seed=seed,
    priors=tuple(priors),
  )


def _parse_sql_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_sql(text))
  except ParseError as exc:
    return Err(str(exc))


def _parse_run_result(text: str) -> Result[Command, str]:
  try:
    return Ok[Command, str](_parse_run(text))
  except ParseError as exc:
    return Err(str(exc))


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

  if parts.name == "bayesplot":
    return _parse_bayesplot(parts)

  if parts.name == "set":
    return _parse_set(parts)

  if parts.name == "save":
    return _parse_save_or_export(parts, "save")

  if parts.name == "export":
    return _parse_save_or_export(parts, "export")

  if parts.name == "regress":
    return _parse_regress(parts)

  if parts.name == "lasso":
    return _parse_lasso(parts)

  if parts.name == "postlasso":
    return _parse_postlasso(parts)

  if parts.name == "ridge":
    return _parse_ridge(parts)

  if parts.name == "elasticnet":
    return _parse_elasticnet(parts)

  if parts.name == "cvlasso":
    return _parse_cvlasso(parts)

  if parts.name == "cvridge":
    return _parse_cvridge(parts)

  if parts.name == "cvelasticnet":
    return _parse_cvelasticnet(parts)

  if parts.name == "bayes":
    return _parse_bayes(parts)

  if parts.name == "spregress":
    return _parse_spregress(parts)

  if parts.name == "qreg":
    return _parse_qreg(parts)

  if parts.name == "logit":
    return _parse_logit(parts)

  if parts.name == "probit":
    return _parse_probit(parts)

  if parts.name == "tobit":
    return _parse_tobit(parts)

  if parts.name == "heckman":
    return _parse_heckman(parts)

  if parts.name == "nl":
    return _parse_nl(parts)

  if parts.name == "poisson":
    return _parse_poisson(parts)

  if parts.name == "nbreg":
    return _parse_nbreg(parts)

  if parts.name == "zip":
    return _parse_zip(parts)

  if parts.name == "zinb":
    return _parse_zinb(parts)

  if parts.name == "streg":
    return _parse_streg(parts)

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

  if parts.name == "xtlogit":
    return _parse_xtlogit(parts)

  if parts.name == "xtabond":
    return _parse_xtabond(parts)

  if parts.name == "lowess":
    return _parse_lowess(parts)

  if parts.name == "did":
    return _parse_did(parts)

  if parts.name == "drdid":
    return _parse_drdid(parts)

  if parts.name == "dml":
    return _parse_dml(parts)

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

  opt_tokens = _tokenize(option_text)
  options = _parse_options(opt_tokens)

  opt_names = [opt.name for opt in options]
  if len(opt_names) != len(set(opt_names)):
    raise ParseError("use option specified more than once")

  is_lazy = "lazy" in {opt.name for opt in options}
  engine = None
  delimiter = None
  has_header = None

  for opt in options:
    if opt.name == "engine":
      if not isinstance(opt.value, str):
        raise ParseError("use engine option expects a string value")
      engine = opt.value.lower()
    elif opt.name == "delimiter":
      if not isinstance(opt.value, str):
        raise ParseError("use delimiter option expects a string value")
      delimiter = opt.value
    elif opt.name == "has_header":
      if not isinstance(opt.value, bool):
        raise ParseError("use has_header option expects a boolean value")
      has_header = opt.value
    elif opt.name == "lazy":
      if opt.value is not True:
        raise ParseError("use lazy option does not accept a value")
    else:
      raise ParseError(f"unknown use option: {opt.name}")

  if engine is not None and engine not in {"duckdb", "polars"}:
    raise ParseError("use engine must be duckdb or polars")
  if engine is not None and not is_lazy:
    raise ParseError("use engine option requires lazy mode")
  lazy_engine = cast(Literal["duckdb", "polars"] | None, engine)

  return UseCommand(
    path=_parse_use_path(path_parts[0]),
    execution_mode="lazy" if is_lazy else "eager",
    lazy_engine=lazy_engine or ("duckdb" if is_lazy else None),
    delimiter=delimiter,
    has_header=has_header,
  )


def _parse_use_path(path_text: str) -> Path | str:
  if _is_remote_uri(path_text):
    return path_text
  return Path(path_text)


def _is_remote_uri(path_text: str) -> bool:
  return "://" in path_text


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
  if parts.expression is not None:
    raise ParseError("tabulate does not accept assignment syntax")

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"row", "col", "missing", "rows", "columns", "values", "stat"}
  if unsupported:
    raise ParseError(f"tabulate unsupported option: {', '.join(sorted(unsupported))}")
  for option in parts.options:
    if option.name in {"row", "col", "missing"} and option.value is not True:
      raise ParseError(f"tabulate option {option.name} does not accept a value")

  explicit_rows = _single_identifier_tuple_option(parts.options, "rows", "tabulate")
  explicit_columns = _single_identifier_tuple_option(parts.options, "columns", "tabulate")
  values = _single_identifier_option(parts.options, "values", "tabulate")
  statistic = _single_stat_option(parts.options)

  if explicit_rows is not None or explicit_columns is not None:
    if parts.arguments:
      raise ParseError("tabulate cannot combine positional variables with rows() or columns()")
    if not explicit_rows:
      raise ParseError("tabulate rows() expects at least one variable")
    row_variables = explicit_rows
    column_variables = explicit_columns or ()
  else:
    if len(parts.arguments) not in {1, 2}:
      raise ParseError("tabulate expects one or two variables or rows()/columns() options")
    row_variables = (parts.arguments[0],)
    column_variables = parts.arguments[1:]

  if (values is None) != (statistic is None):
    raise ParseError("tabulate values() and stat() must be specified together")

  if values is not None and option_names & {"row", "col"}:
    raise ParseError("tabulate row and col percentages are only supported for frequencies")

  if not column_variables and option_names & {"row", "col"}:
    raise ParseError("one-way tabulate does not accept row or col options")

  dimension_variables = row_variables + column_variables
  duplicate_dimensions = _duplicate_names(dimension_variables)
  if duplicate_dimensions:
    raise ParseError(f"tabulate duplicate variable: {duplicate_dimensions[0]}")
  if values is not None and values in dimension_variables:
    raise ParseError("tabulate values() variable cannot also be a row or column variable")

  return TabulateCommand(
    row_variables=row_variables,
    column_variables=column_variables,
    condition=parts.condition,
    value_variable=values,
    statistic=statistic,
    row_percent="row" in option_names,
    column_percent="col" in option_names,
    include_missing="missing" in option_names,
  )


def _single_identifier_tuple_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
) -> tuple[str, ...] | None:
  matching = tuple(option for option in options if option.name == name)
  if len(matching) == 0:
    return None
  if len(matching) > 1:
    raise ParseError(f"{command_name} option {name} can only be specified once")
  (option,) = matching
  value = option.value
  if not isinstance(value, tuple) or not all(isinstance(item, str) for item in value):
    raise ParseError(f"{command_name} option {name} expects identifiers in parentheses")
  if not value:
    raise ParseError(f"{command_name} option {name} expects at least one variable")
  return value


def _single_identifier_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
) -> str | None:
  values = _single_identifier_tuple_option(options, name, command_name)
  if values is None:
    return None
  if len(values) != 1:
    raise ParseError(f"{command_name} option {name} expects exactly one variable")
  return values[0]


def _single_stat_option(
  options: tuple[CommandOption, ...],
) -> Literal["count", "mean", "sum", "min", "max"] | None:
  matching = tuple(option for option in options if option.name == "stat")
  if len(matching) == 0:
    return None
  if len(matching) > 1:
    raise ParseError("tabulate option stat can only be specified once")
  (option,) = matching
  value = option.value
  if not isinstance(value, tuple) or len(value) != 1 or not isinstance(value[0], str):
    raise ParseError("tabulate option stat expects exactly one statistic")
  statistic = value[0].lower()
  if statistic not in _TABULATE_STATS:
    raise ParseError(f"tabulate unsupported stat: {statistic}")
  return cast(Literal["count", "mean", "sum", "min", "max"], statistic)


def _duplicate_names(names: tuple[str, ...]) -> tuple[str, ...]:
  seen: set[str] = set()
  duplicates: list[str] = []
  for name in names:
    if name in seen:
      duplicates.append(name)
    seen.add(name)
  return tuple(duplicates)


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


def _parse_bayesplot(parts: _CommandParts) -> BayesPlotCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("bayesplot does not accept if clauses or assignment syntax")
  if len(parts.arguments) != 1:
    raise ParseError("bayesplot expects syntax: bayesplot <trace|density|autocorrelation>")
  kind = parts.arguments[0]
  if kind not in ("trace", "density", "autocorrelation"):
    raise ParseError("bayesplot kind must be trace, density, or autocorrelation")

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"saving", "noopen"}
  if unsupported:
    raise ParseError(f"bayesplot unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "bayesplot", {"noopen"})

  return BayesPlotCommand(
    kind=cast(Literal["trace", "density", "autocorrelation"], kind),
    saving=_single_path_option(parts.options, "saving", "bayesplot"),
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


def _parse_lasso(parts: _CommandParts) -> LassoCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("lasso expects syntax: lasso linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("lasso expects syntax: lasso linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("lasso model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"alpha", "noconstant"}
  if unsupported:
    raise ParseError(f"lasso unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "lasso", {"noconstant"})
  alpha = _single_float_option(parts.options, "alpha", "lasso")
  if alpha is None:
    alpha = 1.0
  if alpha <= 0.0:
    raise ParseError("lasso option alpha must be positive")
  return LassoCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    alpha=alpha,
    include_intercept="noconstant" not in option_names,
  )


def _parse_postlasso(parts: _CommandParts) -> PostlassoCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("postlasso expects syntax: postlasso linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("postlasso expects syntax: postlasso linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("postlasso model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"alpha", "robust", "noconstant"}
  if unsupported:
    raise ParseError(f"postlasso unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "postlasso", {"robust", "noconstant"})
  alpha = _single_float_option(parts.options, "alpha", "postlasso")
  if alpha is None:
    alpha = 1.0
  if alpha <= 0.0:
    raise ParseError("postlasso option alpha must be positive")
  return PostlassoCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    alpha=alpha,
    robust="robust" in option_names,
    include_intercept="noconstant" not in option_names,
  )


def _parse_ridge(parts: _CommandParts) -> RidgeCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("ridge expects syntax: ridge linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("ridge expects syntax: ridge linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("ridge model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"alpha", "noconstant"}
  if unsupported:
    raise ParseError(f"ridge unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "ridge", {"noconstant"})
  alpha = _single_float_option(parts.options, "alpha", "ridge")
  if alpha is None:
    alpha = 1.0
  if alpha <= 0.0:
    raise ParseError("ridge option alpha must be positive")
  return RidgeCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    alpha=alpha,
    include_intercept="noconstant" not in option_names,
  )


def _parse_elasticnet(parts: _CommandParts) -> ElasticnetCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("elasticnet expects syntax: elasticnet linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("elasticnet expects syntax: elasticnet linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("elasticnet model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"alpha", "l1_ratio", "noconstant"}
  if unsupported:
    raise ParseError(f"elasticnet unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "elasticnet", {"noconstant"})
  alpha = _single_float_option(parts.options, "alpha", "elasticnet")
  if alpha is None:
    alpha = 1.0
  if alpha <= 0.0:
    raise ParseError("elasticnet option alpha must be positive")
  l1_ratio = _single_float_option(parts.options, "l1_ratio", "elasticnet")
  if l1_ratio is None:
    l1_ratio = 0.5
  if not (0.0 <= l1_ratio <= 1.0):
    raise ParseError("elasticnet option l1_ratio must be between 0 and 1 inclusive")
  return ElasticnetCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    alpha=alpha,
    l1_ratio=l1_ratio,
    include_intercept="noconstant" not in option_names,
  )


def _elasticnet_cv_l1_ratio(
  options: tuple[CommandOption, ...], command_name: str
) -> float | tuple[float, ...] | None:
  matched = [o for o in options if o.name == "l1_ratio"]
  if not matched:
    return None
  if len(matched) > 1:
    raise ParseError(f"{command_name} option l1_ratio may only be supplied once")
  val = matched[0].value
  if isinstance(val, tuple):
    if not val:
      raise ParseError(f"{command_name} option l1_ratio cannot be empty")
    parsed: list[float] = []
    for item in val:
      try:
        f = float(item)
      except ValueError as exc:
        raise ParseError(f"{command_name} option l1_ratio values must be numeric") from exc
      if not (0.0 <= f <= 1.0):
        raise ParseError(f"{command_name} option l1_ratio values must be between 0 and 1 inclusive")
      parsed.append(f)
    return tuple(parsed)
  if isinstance(val, bool) or not isinstance(val, (int, float)):
    raise ParseError(
      f"{command_name} option l1_ratio expects a numeric value or list of numeric values"
    )
  f = float(val)
  if not (0.0 <= f <= 1.0):
    raise ParseError(f"{command_name} option l1_ratio values must be between 0 and 1 inclusive")
  return f


def _parse_cvlasso(parts: _CommandParts) -> CvlassoCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("cvlasso expects syntax: cvlasso linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("cvlasso expects syntax: cvlasso linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("cvlasso model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"cv", "noconstant"}
  if unsupported:
    raise ParseError(f"cvlasso unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "cvlasso", {"noconstant"})
  cv = _single_integer_option(parts.options, "cv", "cvlasso", minimum=2)
  if cv is None:
    cv = 5
  return CvlassoCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    cv=cv,
    include_intercept="noconstant" not in option_names,
  )


def _parse_cvridge(parts: _CommandParts) -> CvridgeCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("cvridge expects syntax: cvridge linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("cvridge expects syntax: cvridge linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("cvridge model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"cv", "noconstant"}
  if unsupported:
    raise ParseError(f"cvridge unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "cvridge", {"noconstant"})
  cv = _single_integer_option(parts.options, "cv", "cvridge", minimum=2)
  if cv is None:
    cv = 5
  return CvridgeCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    cv=cv,
    include_intercept="noconstant" not in option_names,
  )


def _parse_cvelasticnet(parts: _CommandParts) -> CvelasticnetCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("cvelasticnet expects syntax: cvelasticnet linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("cvelasticnet expects syntax: cvelasticnet linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("cvelasticnet model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"cv", "l1_ratio", "noconstant"}
  if unsupported:
    raise ParseError(f"cvelasticnet unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "cvelasticnet", {"noconstant"})
  cv = _single_integer_option(parts.options, "cv", "cvelasticnet", minimum=2)
  if cv is None:
    cv = 5
  l1_ratio = _elasticnet_cv_l1_ratio(parts.options, "cvelasticnet")
  if l1_ratio is None:
    l1_ratio = (0.1, 0.5, 0.7, 0.9, 0.95, 0.99, 1.0)
  return CvelasticnetCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    cv=cv,
    l1_ratio=l1_ratio,
    include_intercept="noconstant" not in option_names,
  )


def _parse_bayes(parts: _CommandParts) -> BayesCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("bayes expects syntax: bayes linear <y> <xvars>")
  if len(parts.arguments) < 3:
    raise ParseError("bayes expects syntax: bayes linear <y> <xvars>")
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("bayes model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"n_iter", "tol", "noconstant"}
  if unsupported:
    raise ParseError(f"bayes unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "bayes", {"noconstant"})
  n_iter = _single_integer_option(parts.options, "n_iter", "bayes", minimum=1)
  if n_iter is None:
    n_iter = 300
  tol = _single_float_option(parts.options, "tol", "bayes")
  if tol is None:
    tol = 0.001
  if tol <= 0.0:
    raise ParseError("bayes option tol must be positive")
  return BayesCommand(
    outcome=parts.arguments[1],
    predictors=parts.arguments[2:],
    n_iter=n_iter,
    tol=tol,
    include_intercept="noconstant" not in option_names,
  )


def _parse_spregress(parts: _CommandParts) -> SpregressCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(
      "spregress expects syntax: spregress <y> <xvars>, [coord(<lat_var> <lon_var>) [knn(<k>)] | "
      "weights(<path_to_file>) id(<id_var>) [contiguity(queen|rook)]] "
      "[model(<lag|error|sarar>) robust]"
    )
  if len(parts.arguments) < 2:
    raise ParseError(
      "spregress expects syntax: spregress <y> <xvars>, [coord(<lat_var> <lon_var>) [knn(<k>)] | "
      "weights(<path_to_file>) id(<id_var>) [contiguity(queen|rook)]] "
      "[model(<lag|error|sarar>) robust]"
    )

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"coord", "model", "knn", "robust", "weights", "id", "contiguity"}
  if unsupported:
    raise ParseError(f"spregress unsupported option: {', '.join(sorted(unsupported))}")

  _require_flag_options(parts.options, "spregress", {"robust"})

  has_coord = "coord" in option_names
  has_weights = "weights" in option_names

  if has_coord and has_weights:
    raise ParseError("spregress option coord and weights are mutually exclusive")
  elif not has_coord and not has_weights:
    raise ParseError("spregress requires either coord() or weights() option")

  model_type_val: Literal["lag", "error", "sarar"] | str = (
    _single_text_option(parts.options, "model", "spregress") or "lag"
  )
  if model_type_val not in ("lag", "error", "sarar"):
    raise ParseError("spregress option model must be 'lag', 'error', or 'sarar'")
  model_type: Literal["lag", "error", "sarar"] = model_type_val

  if has_coord:
    if "id" in option_names:
      raise ParseError("spregress option id can only be used with weights() option")
    if "contiguity" in option_names:
      raise ParseError("spregress option contiguity can only be used with weights() option")

    coord_values = _single_tuple_option(parts.options, "coord", "spregress")
    if coord_values is None or len(coord_values) != 2:
      raise ParseError(
        "spregress option coord expects exactly two variables representing "
        "latitude and longitude coordinates"
      )

    knn_val = _single_integer_option(parts.options, "knn", "spregress", minimum=1)
    if knn_val is None:
      knn_val = 5

    return SpregressCommand(
      outcome=parts.arguments[0],
      predictors=parts.arguments[1:],
      model_type=model_type,
      coord_variables=coord_values,
      knn=knn_val,
      robust="robust" in option_names,
    )
  else:
    # weights is specified
    if "knn" in option_names or "coord" in option_names:
      raise ParseError("spregress option knn/coord can only be used with coord() option")

    weights_path = _single_path_option(parts.options, "weights", "spregress")
    if weights_path is None:
      raise ParseError("spregress option weights() expects a path")

    id_var = _single_text_option(parts.options, "id", "spregress")
    if id_var is None:
      raise ParseError("spregress option id() is required when weights() is specified")

    contiguity_val = _single_text_option(parts.options, "contiguity", "spregress") or "queen"
    if contiguity_val not in ("queen", "rook"):
      raise ParseError("spregress option contiguity must be 'queen' or 'rook'")
    contiguity: Literal["queen", "rook"] = contiguity_val

    return SpregressCommand(
      outcome=parts.arguments[0],
      predictors=parts.arguments[1:],
      model_type=model_type,
      weights_file=str(weights_path),
      id_variable=id_var,
      contiguity=contiguity,
      robust="robust" in option_names,
    )


def _parse_qreg(parts: _CommandParts) -> QregCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("qreg expects syntax: qreg <y> <xvars>")
  if len(parts.arguments) < 2:
    raise ParseError("qreg expects syntax: qreg <y> <xvars>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"quantile", "robust", "noconstant"}
  if unsupported:
    raise ParseError(f"qreg unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "qreg", {"robust", "noconstant"})
  quantile = _single_float_option(parts.options, "quantile", "qreg")
  if quantile is None:
    quantile = 0.5
  if quantile <= 0.0 or quantile >= 1.0:
    raise ParseError("qreg option quantile must be between 0 and 1")
  return QregCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    quantile=quantile,
    robust="robust" in option_names,
    include_intercept="noconstant" not in option_names,
  )


def _parse_predict(parts: _CommandParts) -> PredictCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("predict expects syntax: predict <newvar>")
  if len(parts.arguments) != 1:
    raise ParseError("predict expects syntax: predict <newvar>")
  option_names = {option.name for option in parts.options}
  predict_kinds = {"xb", "residuals", "pr", "spatial_lag", "posterior_predictive"}
  predict_aux_options = {"interval", "level"}
  unsupported = option_names - predict_kinds - predict_aux_options
  if unsupported:
    raise ParseError(f"predict unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "predict", predict_kinds)
  _require_flag_options(parts.options, "predict", {"interval"})
  selected_kinds = predict_kinds & option_names
  if len(selected_kinds) > 1:
    raise ParseError(
      "predict options xb, residuals, pr, spatial_lag, and posterior_predictive cannot be combined"
    )
  kind: Literal["xb", "residuals", "pr", "spatial_lag", "posterior_predictive"] = "xb"
  if "residuals" in option_names:
    kind = "residuals"
  if "pr" in option_names:
    kind = "pr"
  if "spatial_lag" in option_names:
    kind = "spatial_lag"
  if "posterior_predictive" in option_names:
    kind = "posterior_predictive"
  interval = "interval" in option_names
  level = _single_float_option(parts.options, "level", "predict")
  if level is None:
    level = 95.0
  if (interval or "level" in option_names) and kind != "posterior_predictive":
    raise ParseError("predict interval options require posterior_predictive")
  if "level" in option_names and not interval:
    raise ParseError("predict option level requires interval")
  if level <= 0.0 or level >= 100.0:
    raise ParseError("predict option level must be between 0 and 100")
  return PredictCommand(
    target_variable=parts.arguments[0],
    kind=kind,
    interval=interval,
    level=level,
  )


def _parse_logit(parts: _CommandParts) -> LogitCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("logit expects syntax: logit <y> <xvars>")
  if len(parts.arguments) < 2:
    raise ParseError("logit expects syntax: logit <y> <xvars>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"logit unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "logit", {"robust", "noconstant"})
  cluster_values = _single_tuple_option(parts.options, "cluster", "logit")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("logit option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("logit cannot combine robust and cluster")
  return LogitCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_probit(parts: _CommandParts) -> ProbitCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("probit expects syntax: probit <y> <xvars>")
  if len(parts.arguments) < 2:
    raise ParseError("probit expects syntax: probit <y> <xvars>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"probit unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "probit", {"robust", "noconstant"})
  cluster_values = _single_tuple_option(parts.options, "cluster", "probit")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("probit option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("probit cannot combine robust and cluster")
  return ProbitCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_tobit(parts: _CommandParts) -> TobitCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("tobit expects syntax: tobit <y> <xvars>, ll(<num>) [ul(<num>)]")
  if len(parts.arguments) < 2:
    raise ParseError("tobit expects syntax: tobit <y> <xvars>, ll(<num>) [ul(<num>)]")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"ll", "ul", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"tobit unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "tobit", {"robust", "noconstant"})
  lower_limit = _single_float_option(parts.options, "ll", "tobit")
  if lower_limit is None:
    raise ParseError("tobit option ll expects one numeric value")
  upper_limit = _single_float_option(parts.options, "ul", "tobit")
  cluster_values = _single_tuple_option(parts.options, "cluster", "tobit")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("tobit option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("tobit cannot combine robust and cluster")
  return TobitCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    lower_limit=lower_limit,
    upper_limit=upper_limit,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_heckman(parts: _CommandParts) -> HeckmanCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("heckman expects syntax: heckman <y> <xvars>, selectdep(<var>) select(<vars>)")
  if len(parts.arguments) < 2:
    raise ParseError("heckman expects syntax: heckman <y> <xvars>, selectdep(<var>) select(<vars>)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"selectdep", "select", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"heckman unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "heckman", {"robust", "noconstant"})
  selectdep_values = _single_tuple_option(parts.options, "selectdep", "heckman")
  if selectdep_values is None or len(selectdep_values) != 1:
    raise ParseError("heckman option selectdep expects one variable")
  select_values = _single_tuple_option(parts.options, "select", "heckman")
  if select_values is None:
    raise ParseError("heckman option select expects at least one variable")
  cluster_values = _single_tuple_option(parts.options, "cluster", "heckman")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("heckman option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("heckman cannot combine robust and cluster")
  return HeckmanCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    selection_dependent=selectdep_values[0],
    selection_predictors=select_values,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_nl(parts: _CommandParts) -> NlCommand:
  if parts.condition is not None:
    raise ParseError("nl expects syntax: nl <y> = <expr>, params(<params>) start(<values>)")
  if len(parts.arguments) != 1 or parts.expression is None:
    raise ParseError("nl expects syntax: nl <y> = <expr>, params(<params>) start(<values>)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"params", "start", "robust", "noconstant"}
  if unsupported:
    raise ParseError(f"nl unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "nl", {"robust", "noconstant"})
  params_values = _single_tuple_option(parts.options, "params", "nl")
  if params_values is None:
    raise ParseError("nl option params expects one-or-more parameter names")
  if len(set(params_values)) != len(params_values):
    raise ParseError("nl option params must not repeat parameter names")
  start_values_raw = _single_tuple_option(parts.options, "start", "nl")
  if start_values_raw is None:
    raise ParseError("nl option start expects one-or-more numeric values")
  try:
    start_values = tuple(float(value) for value in start_values_raw)
  except ValueError as exc:
    raise ParseError("nl option start expects one-or-more numeric values") from exc
  if len(start_values) != len(params_values):
    raise ParseError("nl option start count must match params count")
  return NlCommand(
    outcome=parts.arguments[0],
    expression=parts.expression,
    parameter_names=params_values,
    start_values=start_values,
    robust="robust" in option_names,
    include_intercept="noconstant" not in option_names,
  )


def _parse_poisson(parts: _CommandParts) -> PoissonCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("poisson expects syntax: poisson <y> <xvars>")
  if len(parts.arguments) < 2:
    raise ParseError("poisson expects syntax: poisson <y> <xvars>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"poisson unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "poisson", {"robust", "noconstant"})
  cluster_values = _single_tuple_option(parts.options, "cluster", "poisson")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("poisson option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("poisson cannot combine robust and cluster")
  return PoissonCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_nbreg(parts: _CommandParts) -> NbregCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("nbreg expects syntax: nbreg <y> <xvars>")
  if len(parts.arguments) < 2:
    raise ParseError("nbreg expects syntax: nbreg <y> <xvars>")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"nbreg unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "nbreg", {"robust", "noconstant"})
  cluster_values = _single_tuple_option(parts.options, "cluster", "nbreg")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("nbreg option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("nbreg cannot combine robust and cluster")
  return NbregCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_zip(parts: _CommandParts) -> ZipCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("zip expects syntax: zip <y> <xvars>, inflate(<zvars>)")
  if len(parts.arguments) < 2:
    raise ParseError("zip expects syntax: zip <y> <xvars>, inflate(<zvars>)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"inflate", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"zip unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "zip", {"robust", "noconstant"})
  inflate_values = _single_tuple_option(parts.options, "inflate", "zip")
  if inflate_values is None:
    raise ParseError("zip option inflate expects one-or-more variables")
  cluster_values = _single_tuple_option(parts.options, "cluster", "zip")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("zip option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("zip cannot combine robust and cluster")
  return ZipCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    inflate_predictors=inflate_values,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_zinb(parts: _CommandParts) -> ZinbCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("zinb expects syntax: zinb <y> <xvars>, inflate(<zvars>)")
  if len(parts.arguments) < 2:
    raise ParseError("zinb expects syntax: zinb <y> <xvars>, inflate(<zvars>)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"inflate", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"zinb unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "zinb", {"robust", "noconstant"})
  inflate_values = _single_tuple_option(parts.options, "inflate", "zinb")
  if inflate_values is None:
    raise ParseError("zinb option inflate expects one-or-more variables")
  cluster_values = _single_tuple_option(parts.options, "cluster", "zinb")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("zinb option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("zinb cannot combine robust and cluster")
  return ZinbCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    inflate_predictors=inflate_values,
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_streg(parts: _CommandParts) -> StregCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("streg expects syntax: streg <time_var> <xvars>, failure(<event>) dist(...)")
  if len(parts.arguments) < 2:
    raise ParseError("streg expects syntax: streg <time_var> <xvars>, failure(<event>) dist(...)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"failure", "dist", "robust", "cluster", "noconstant"}
  if unsupported:
    raise ParseError(f"streg unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "streg", {"robust", "noconstant"})
  failure_values = _single_tuple_option(parts.options, "failure", "streg")
  if failure_values is None or len(failure_values) != 1:
    raise ParseError("streg option failure expects one variable")
  dist_values = _single_tuple_option(parts.options, "dist", "streg")
  if dist_values is None or len(dist_values) != 1:
    raise ParseError("streg option dist expects one value")
  distribution = dist_values[0].lower()
  if distribution not in {"weibull", "exponential"}:
    raise ParseError("streg option dist must be weibull or exponential")
  cluster_values = _single_tuple_option(parts.options, "cluster", "streg")
  if cluster_values is not None and len(cluster_values) != 1:
    raise ParseError("streg option cluster expects one variable")
  robust = "robust" in option_names
  cluster_variable = cluster_values[0] if cluster_values is not None else None
  if robust and cluster_variable is not None:
    raise ParseError("streg cannot combine robust and cluster")
  return StregCommand(
    time_variable=parts.arguments[0],
    predictors=parts.arguments[1:],
    failure_variable=failure_values[0],
    distribution=cast(Literal["weibull", "exponential"], distribution),
    robust=robust,
    cluster_variable=cluster_variable,
    include_intercept="noconstant" not in option_names,
  )


def _parse_estat(parts: _CommandParts) -> EstatCommand:
  expected_estat_syntax = (
    "estat expects syntax: "
    "estat <residuals|ovtest|vif|firststage|overid|hausman|endogenous|margins|gof|did|drdid|"
    "dml|bayes|spatial>"
  )
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(expected_estat_syntax)
  if len(parts.arguments) != 1:
    raise ParseError(expected_estat_syntax)
  subcommand = parts.arguments[0].lower()
  if subcommand not in {
    "residuals",
    "ovtest",
    "vif",
    "firststage",
    "overid",
    "hausman",
    "endogenous",
    "margins",
    "gof",
    "did",
    "drdid",
    "dml",
    "bayes",
    "spatial",
  }:
    raise ParseError(
      "estat subcommand must be residuals, ovtest, vif, firststage, "
      "overid, hausman, endogenous, margins, gof, did, drdid, dml, bayes, or spatial"
    )

  if subcommand != "spatial":
    if parts.options:
      raise ParseError(f"estat {subcommand} does not support options")
    return EstatCommand(
      subcommand=cast(
        Literal[
          "residuals",
          "ovtest",
          "vif",
          "firststage",
          "overid",
          "hausman",
          "endogenous",
          "margins",
          "gof",
          "did",
          "drdid",
          "dml",
          "bayes",
        ],
        subcommand,
      )
    )

  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"coord", "knn", "weights", "id", "contiguity"}
  if unsupported:
    raise ParseError(f"estat spatial unsupported option: {', '.join(sorted(unsupported))}")

  has_coord = "coord" in option_names
  has_weights = "weights" in option_names

  if has_coord and has_weights:
    raise ParseError("estat spatial option coord and weights are mutually exclusive")
  elif not has_coord and not has_weights:
    raise ParseError("estat spatial requires either coord() or weights() option")

  if has_coord:
    if "id" in option_names:
      raise ParseError("estat spatial option id can only be used with weights() option")
    if "contiguity" in option_names:
      raise ParseError("estat spatial option contiguity can only be used with weights() option")

    coord_values = _single_tuple_option(parts.options, "coord", "estat spatial")
    if coord_values is None or len(coord_values) != 2:
      raise ParseError(
        "estat spatial option coord expects exactly two variables representing "
        "latitude and longitude coordinates"
      )

    knn_val = _single_integer_option(parts.options, "knn", "estat spatial", minimum=1)
    if knn_val is None:
      knn_val = 5

    return EstatCommand(
      subcommand="spatial",
      coord_variables=coord_values,
      knn=knn_val,
    )
  else:
    # weights is specified
    if "knn" in option_names or "coord" in option_names:
      raise ParseError("estat spatial option knn/coord can only be used with coord() option")

    weights_path = _single_path_option(parts.options, "weights", "estat spatial")
    if weights_path is None:
      raise ParseError("estat spatial option weights() expects a path")

    id_var = _single_text_option(parts.options, "id", "estat spatial")
    if id_var is None:
      raise ParseError("estat spatial option id() is required when weights() is specified")

    contiguity_val = _single_text_option(parts.options, "contiguity", "estat spatial") or "queen"
    if contiguity_val not in ("queen", "rook"):
      raise ParseError("estat spatial option contiguity must be 'queen' or 'rook'")
    contiguity: Literal["queen", "rook"] = contiguity_val

    return EstatCommand(
      subcommand="spatial",
      weights_file=str(weights_path),
      id_variable=id_var,
      contiguity=contiguity,
    )


def _parse_ivregress(parts: _CommandParts) -> IvRegressCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(
      "ivregress expects syntax: ivregress 2sls|gmm <y> [exog_vars], endog(<var>) iv(<vars>)"
    )
  if len(parts.arguments) < 2:
    raise ParseError(
      "ivregress expects syntax: ivregress 2sls|gmm <y> [exog_vars], endog(<var>) iv(<vars>)"
    )
  estimator = parts.arguments[0].lower()
  if estimator not in {"2sls", "gmm"}:
    raise ParseError("ivregress estimator must be 2sls or gmm")
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
    estimator=cast(Literal["2sls", "gmm"], estimator),
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


def _parse_xtlogit(parts: _CommandParts) -> XtLogitCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("xtlogit expects syntax: xtlogit <y> <xvars>, fe [robust]")
  if len(parts.arguments) < 2:
    raise ParseError("xtlogit expects syntax: xtlogit <y> <xvars>, fe [robust]")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"fe", "robust"}
  if unsupported:
    raise ParseError(f"xtlogit unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "xtlogit", {"fe", "robust"})
  if "fe" not in option_names:
    raise ParseError("xtlogit requires option fe")
  return XtLogitCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    robust="robust" in option_names,
  )


def _parse_xtabond(parts: _CommandParts) -> XtAbondCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("xtabond expects syntax: xtabond <y> [xvars] [, robust lags(#) instlag(#)]")
  if len(parts.arguments) < 1:
    raise ParseError("xtabond expects syntax: xtabond <y> [xvars] [, robust lags(#) instlag(#)]")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"robust", "lags", "instlag"}
  if unsupported:
    raise ParseError(f"xtabond unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "xtabond", {"robust"})
  lag_depth = _single_integer_option(parts.options, "lags", "xtabond", minimum=1)
  instrument_lag_start = _single_integer_option(parts.options, "instlag", "xtabond", minimum=2)
  resolved_lag_depth = lag_depth if lag_depth is not None else 1
  resolved_instlag = instrument_lag_start if instrument_lag_start is not None else 2
  if resolved_instlag <= resolved_lag_depth:
    raise ParseError("xtabond option instlag must be greater than option lags")
  return XtAbondCommand(
    outcome=parts.arguments[0],
    predictors=parts.arguments[1:],
    robust="robust" in option_names,
    lag_depth=resolved_lag_depth,
    instrument_lag_start=resolved_instlag,
  )


def _parse_lowess(parts: _CommandParts) -> LowessCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("lowess expects syntax: lowess <y> <x>, gen(<newvar>) [bandwidth=<0,1>]")
  if len(parts.arguments) != 2:
    raise ParseError("lowess expects syntax: lowess <y> <x>, gen(<newvar>) [bandwidth=<0,1>]")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"gen", "bandwidth"}
  if unsupported:
    raise ParseError(f"lowess unsupported option: {', '.join(sorted(unsupported))}")
  gen_values = _single_tuple_option(parts.options, "gen", "lowess")
  if gen_values is None or len(gen_values) != 1:
    raise ParseError("lowess option gen expects one variable")
  bandwidth = _single_float_option(parts.options, "bandwidth", "lowess")
  resolved_bandwidth = float(bandwidth) if bandwidth is not None else (2.0 / 3.0)
  if not (0.0 < resolved_bandwidth < 1.0):
    raise ParseError("lowess option bandwidth must be between 0 and 1")
  return LowessCommand(
    outcome=parts.arguments[0],
    predictor=parts.arguments[1],
    target_variable=gen_values[0],
    bandwidth=resolved_bandwidth,
  )


def _parse_did(parts: _CommandParts) -> DidCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError("did expects syntax: did <y> [controls], treat(<var>) post(<var>)")
  if not parts.arguments:
    raise ParseError("did expects syntax: did <y> [controls], treat(<var>) post(<var>)")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"treat", "post", "robust"}
  if unsupported:
    raise ParseError(f"did unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "did", {"robust"})
  treat_values = _single_tuple_option(parts.options, "treat", "did")
  if treat_values is None or len(treat_values) != 1:
    raise ParseError("did option treat expects one variable")
  post_values = _single_tuple_option(parts.options, "post", "did")
  if post_values is None or len(post_values) != 1:
    raise ParseError("did option post expects one variable")
  treatment_variable = treat_values[0]
  post_variable = post_values[0]
  if treatment_variable == post_variable:
    raise ParseError("did treatment and post variables must be distinct")
  outcome = parts.arguments[0]
  controls = parts.arguments[1:]
  if treatment_variable == outcome or post_variable == outcome:
    raise ParseError("did treatment and post variables must differ from outcome")
  if treatment_variable in controls or post_variable in controls:
    raise ParseError("did treatment and post variables must not appear in controls")
  return DidCommand(
    outcome=outcome,
    controls=controls,
    treatment_variable=treatment_variable,
    post_variable=post_variable,
    robust="robust" in option_names,
  )


def _parse_drdid(parts: _CommandParts) -> DrDidCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(
      "drdid expects syntax: drdid <y> [covariates], treat(<var>) post(<var>) "
      "[method(or|ipw|aipw) robust bootstrap(<n>) seed(<n>)]"
    )
  if not parts.arguments:
    raise ParseError(
      "drdid expects syntax: drdid <y> [covariates], treat(<var>) post(<var>) "
      "[method(or|ipw|aipw) robust bootstrap(<n>) seed(<n>)]"
    )
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"treat", "post", "method", "robust", "bootstrap", "seed"}
  if unsupported:
    raise ParseError(f"drdid unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "drdid", {"robust"})
  treat_values = _single_tuple_option(parts.options, "treat", "drdid")
  if treat_values is None or len(treat_values) != 1:
    raise ParseError("drdid option treat expects one variable")
  post_values = _single_tuple_option(parts.options, "post", "drdid")
  if post_values is None or len(post_values) != 1:
    raise ParseError("drdid option post expects one variable")
  treatment_variable = treat_values[0]
  post_variable = post_values[0]
  if treatment_variable == post_variable:
    raise ParseError("drdid treatment and post variables must be distinct")
  outcome = parts.arguments[0]
  covariates = parts.arguments[1:]
  if treatment_variable == outcome or post_variable == outcome:
    raise ParseError("drdid treatment and post variables must differ from outcome")
  if treatment_variable in covariates or post_variable in covariates:
    raise ParseError("drdid treatment and post variables must not appear in covariates")
  method_str = _single_text_option(parts.options, "method", "drdid")
  method: Literal["or", "ipw", "aipw"] = "aipw"
  if method_str is not None:
    if method_str not in {"or", "ipw", "aipw"}:
      raise ParseError("drdid option method must be one of: or, ipw, aipw")
    method = method_str  # type: ignore
  bootstrap = _single_integer_option(parts.options, "bootstrap", "drdid", minimum=1)
  seed = _single_integer_option(parts.options, "seed", "drdid", minimum=0)
  if seed is not None and bootstrap is None:
    raise ParseError("drdid option seed requires option bootstrap")
  return DrDidCommand(
    outcome=outcome,
    covariates=covariates,
    treatment_variable=treatment_variable,
    post_variable=post_variable,
    method=method,
    robust="robust" in option_names,
    bootstrap=bootstrap,
    seed=seed,
  )


def _parse_dml(parts: _CommandParts) -> DmlCommand:
  if parts.condition is not None or parts.expression is not None:
    raise ParseError(
      "dml expects syntax: dml linear <y> <controls>, treat(<var>) "
      "[folds(<int>) alpha(<num>) robust seed(<int>) noconstant]"
    )
  if len(parts.arguments) < 3:
    raise ParseError(
      "dml expects syntax: dml linear <y> <controls>, treat(<var>) "
      "[folds(<int>) alpha(<num>) robust seed(<int>) noconstant]"
    )
  model = parts.arguments[0].lower()
  if model != "linear":
    raise ParseError("dml model must be linear")
  option_names = {option.name for option in parts.options}
  unsupported = option_names - {"treat", "folds", "alpha", "robust", "seed", "noconstant"}
  if unsupported:
    raise ParseError(f"dml unsupported option: {', '.join(sorted(unsupported))}")
  _require_flag_options(parts.options, "dml", {"robust", "noconstant"})
  treat_values = _single_tuple_option(parts.options, "treat", "dml")
  if treat_values is None or len(treat_values) != 1:
    raise ParseError("dml option treat expects one variable")
  treatment_variable = treat_values[0]
  outcome = parts.arguments[1]
  controls = parts.arguments[2:]
  if treatment_variable == outcome:
    raise ParseError("dml treatment variable must differ from outcome")
  if treatment_variable in controls:
    raise ParseError("dml treatment variable must not appear in controls")
  folds = _single_integer_option(parts.options, "folds", "dml", minimum=2)
  if folds is None:
    folds = 5
  alpha = _single_float_option(parts.options, "alpha", "dml")
  if alpha is None:
    alpha = 1.0
  if alpha <= 0.0:
    raise ParseError("dml option alpha must be positive")
  seed = _single_integer_option(parts.options, "seed", "dml", minimum=0)
  return DmlCommand(
    outcome=outcome,
    controls=controls,
    treatment_variable=treatment_variable,
    folds=folds,
    alpha=alpha,
    robust="robust" in option_names,
    seed=seed,
    include_intercept="noconstant" not in option_names,
  )


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
  parsed_value: int
  if isinstance(value, tuple):
    if len(value) != 1:
      raise ParseError(f"{command_name} option {name} expects one integer value")
    item = value[0]
    if not item.isascii() or not item.isdigit():
      raise ParseError(f"{command_name} option {name} expects an integer value")
    parsed_value = int(item)
  elif isinstance(value, bool):
    raise ParseError(f"{command_name} option {name} expects an integer value")
  elif isinstance(value, float):
    if not value.is_integer():
      raise ParseError(f"{command_name} option {name} expects an integer value")
    parsed_value = int(value)
  elif not isinstance(value, int):
    raise ParseError(f"{command_name} option {name} expects an integer value")
  else:
    parsed_value = value
  if parsed_value < minimum:
    raise ParseError(f"{command_name} option {name} must be at least {minimum}")
  return parsed_value


def _single_float_option(
  options: tuple[CommandOption, ...],
  name: str,
  command_name: str,
) -> float | None:
  matched = [option for option in options if option.name == name]
  if not matched:
    return None
  if len(matched) > 1:
    raise ParseError(f"{command_name} option {name} may only be supplied once")
  value = matched[0].value
  if isinstance(value, tuple):
    if len(value) != 1:
      raise ParseError(f"{command_name} option {name} expects one value")
    try:
      return float(value[0])
    except ValueError as exc:
      raise ParseError(f"{command_name} option {name} expects a numeric value") from exc
  if isinstance(value, bool) or not isinstance(value, (int, float)):
    raise ParseError(f"{command_name} option {name} expects a numeric value")
  return float(value)


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
      depth = 1
      while not stream.at_end and depth > 0:
        peek_text = stream.peek.text
        if peek_text == "(":
          depth += 1
        elif peek_text == ")":
          depth -= 1
          if depth == 0:
            stream.consume()
            break
        value_tokens.append(stream.consume())
      if depth > 0:
        raise ParseError(f"option {name.text} is missing closing )")
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
) -> str | float | bool | tuple[str, ...]:
  if option_name in {"saving", "weights"}:
    return "".join(token.text for token in tokens)

  if option_name == "delimiter":
    if len(tokens) != 1 or tokens[0].kind not in {"string", "identifier"}:
      raise ParseError("option delimiter expects a single string or identifier value")
    return tokens[0].text

  if option_name == "has_header":
    if (
      len(tokens) != 1
      or tokens[0].kind != "identifier"
      or tokens[0].text.lower() not in {"true", "false"}
    ):
      raise ParseError("option has_header expects true or false")
    # Return bool value directly since _parenthesized_option_value return type supports bool.
    return tokens[0].text.lower() == "true"
  if option_name in {
    "alpha",
    "ll",
    "ul",
    "quantile",
    "lags",
    "instlag",
    "n_iter",
    "tol",
    "knn",
    "cv",
    "bootstrap",
    "seed",
    "rseed",
    "folds",
    "level",
    "draws",
    "burnin",
    "tune",
    "chains",
    "thin",
  }:
    numeric_text = "".join(token.text for token in tokens)
    try:
      return float(numeric_text)
    except ValueError as exc:
      raise ParseError(f"option {option_name} expects a numeric value") from exc

  if option_name == "prior":
    if not tokens:
      raise ParseError("prior option expects prior(variable, distribution)")
    comma_index = -1
    for i, token in enumerate(tokens):
      if token.text == ",":
        comma_index = i
        break
    if comma_index <= 0 or comma_index == len(tokens) - 1:
      raise ParseError("prior option expects prior(variable, distribution) syntax")
    var_name = "".join(t.text for t in tokens[:comma_index]).strip()
    dist_expr = "".join(t.text for t in tokens[comma_index + 1 :]).strip()
    return (var_name, dist_expr)
  if option_name == "l1_ratio":
    l1_ratio_values: list[str] = []
    index = 0
    while index < len(tokens):
      token = tokens[index]
      if token.kind == "number":
        l1_ratio_values.append(token.text)
        index += 1
        continue
      if (
        token.kind == "symbol"
        and token.text in {"-", "+"}
        and index + 1 < len(tokens)
        and tokens[index + 1].kind == "number"
      ):
        l1_ratio_values.append(f"{token.text}{tokens[index + 1].text}")
        index += 2
        continue
      raise ParseError("option l1_ratio values must be numeric")
    if len(l1_ratio_values) == 1:
      try:
        return float(l1_ratio_values[0])
      except ValueError as exc:
        raise ParseError("option l1_ratio expects a numeric value") from exc
    return tuple(l1_ratio_values)

  if option_name == "start":
    values: list[str] = []
    index = 0
    while index < len(tokens):
      token = tokens[index]
      if token.kind == "number":
        values.append(token.text)
        index += 1
        continue
      if (
        token.kind == "symbol"
        and token.text in {"-", "+"}
        and index + 1 < len(tokens)
        and tokens[index + 1].kind == "number"
      ):
        values.append(f"{token.text}{tokens[index + 1].text}")
        index += 2
        continue
      raise ParseError(f"option {option_name} values must be numeric")
    return tuple(values)

  identifier_values: list[str] = []
  for token in tokens:
    if token.kind != "identifier":
      raise ParseError(f"option {option_name} values must be identifiers")
    identifier_values.append(token.text)
  return tuple(identifier_values)


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


def _parse_test(text: str) -> TestCommand:
  body = text.strip()[4:].strip()
  if not body:
    raise ParseError("test command expects a list of variables or constraints")

  tokens = _tokenize(body)
  has_parens = any(t.text == "(" for t in tokens)
  constraints: list[Expression] = []

  if has_parens:
    groups: list[tuple[_Token, ...]] = []
    current_group: list[_Token] = []
    depth = 0
    for token in tokens:
      if token.text == "(":
        if depth == 0:
          current_group = []
        else:
          current_group.append(token)
        depth += 1
      elif token.text == ")":
        depth -= 1
        if depth == 0:
          groups.append(tuple(current_group))
        else:
          current_group.append(token)
      else:
        if depth > 0:
          current_group.append(token)
        else:
          raise ParseError("test command: unexpected tokens outside parentheses")
    if depth != 0:
      raise ParseError("test command: mismatched parentheses")

    for group_tokens in groups:
      if not group_tokens:
        raise ParseError("test command: empty constraint inside parentheses")
      constraints.append(_parse_single_constraint(group_tokens))
  else:
    equal_indices = [i for i, t in enumerate(tokens) if t.text in {"=", "=="}]
    if equal_indices:
      if len(equal_indices) > 1:
        raise ParseError(
          "test command: multiple '=' in a single constraint "
          "(use parentheses for multiple constraints)"
        )
      eq_idx = equal_indices[0]
      lhs_tokens = tokens[:eq_idx]
      rhs_tokens = tokens[eq_idx + 1 :]
      if not lhs_tokens:
        raise ParseError("test command: missing left-hand side of constraint")
      if not rhs_tokens:
        raise ParseError("test command: missing right-hand side of constraint")
      lhs = _ExpressionParser(lhs_tokens).parse_all()
      rhs = _ExpressionParser(rhs_tokens).parse_all()
      constraints.append(BinaryExpression(left=lhs, operator="-", right=rhs))
    else:
      for token in tokens:
        if token.kind != "identifier":
          raise ParseError(f"test command: expected variable name, got '{token.text}'")
        constraints.append(IdentifierExpression(token.text))

  return TestCommand(constraints=tuple(constraints))


def _parse_single_constraint(tokens: tuple[_Token, ...]) -> Expression:
  equal_indices = [i for i, t in enumerate(tokens) if t.text in {"=", "=="}]
  if equal_indices:
    if len(equal_indices) > 1:
      raise ParseError("test command: multiple '=' in a constraint")
    eq_idx = equal_indices[0]
    lhs_tokens = tokens[:eq_idx]
    rhs_tokens = tokens[eq_idx + 1 :]
    if not lhs_tokens or not rhs_tokens:
      raise ParseError("test command: malformed constraint")
    lhs = _ExpressionParser(lhs_tokens).parse_all()
    rhs = _ExpressionParser(rhs_tokens).parse_all()
    return BinaryExpression(left=lhs, operator="-", right=rhs)
  else:
    return _ExpressionParser(tokens).parse_all()


def _parse_lincom(text: str) -> LincomCommand:
  body = text.strip()[6:].strip()
  if not body:
    raise ParseError("lincom command expects a linear combination expression")
  tokens = _tokenize(body)
  expression = _ExpressionParser(tokens).parse_all()
  return LincomCommand(expression=expression)


def _parse_ttest(text: str) -> TtestCommand:
  body = text.strip()[5:].strip()
  if not body:
    raise ParseError("ttest command expects a variable comparison or a variable with by() option")

  tokens = _tokenize(body)
  comma_indices = [i for i, t in enumerate(tokens) if t.text == ","]

  if comma_indices:
    if len(comma_indices) > 1:
      raise ParseError("ttest command: duplicate comma")
    c_idx = comma_indices[0]
    var_tokens = tokens[:c_idx]
    opt_tokens = tokens[c_idx + 1 :]

    if len(var_tokens) != 1 or var_tokens[0].kind != "identifier":
      raise ParseError("ttest command: expects a single variable name before comma")
    varname1 = var_tokens[0].text

    options = _parse_options(opt_tokens)
    by_values = _single_tuple_option(options, "by", "ttest")
    if by_values is None or len(by_values) != 1:
      raise ParseError("ttest command requires option by(<variable>)")
    by_variable = by_values[0]

    option_names = {opt.name for opt in options}
    unsupported = option_names - {"by", "welch", "unequal"}
    if unsupported:
      raise ParseError(f"ttest unsupported option: {', '.join(sorted(unsupported))}")

    _require_flag_options(options, "ttest", {"welch", "unequal"})
    welch = "welch" in option_names or "unequal" in option_names

    return TtestCommand(varname1=varname1, by_variable=by_variable, welch=welch)

  else:
    equal_indices = [i for i, t in enumerate(tokens) if t.text in {"=", "=="}]
    if not equal_indices:
      raise ParseError("ttest command expects comparison (e.g. ttest var == value) or by() option")
    if len(equal_indices) > 1:
      raise ParseError("ttest command: multiple comparisons")

    eq_idx = equal_indices[0]
    lhs_tokens = tokens[:eq_idx]
    rhs_tokens = tokens[eq_idx + 1 :]

    if len(lhs_tokens) != 1 or lhs_tokens[0].kind != "identifier":
      raise ParseError("ttest command: LHS must be a single variable name")
    varname1 = lhs_tokens[0].text

    is_signed_number = False
    if len(rhs_tokens) == 2:
      if rhs_tokens[0].text in {"-", "+"} and rhs_tokens[1].kind == "number":
        is_signed_number = True

    if len(rhs_tokens) == 1:
      rhs_token = rhs_tokens[0]
      if rhs_token.kind == "number":
        val = float(rhs_token.text)
        return TtestCommand(varname1=varname1, value=val)
      elif rhs_token.kind == "identifier":
        return TtestCommand(varname1=varname1, varname2=rhs_token.text)
      else:
        raise ParseError("ttest command: RHS must be a variable name or a numeric value")
    elif is_signed_number:
      sign = -1.0 if rhs_tokens[0].text == "-" else 1.0
      val = sign * float(rhs_tokens[1].text)
      return TtestCommand(varname1=varname1, value=val)
    else:
      raise ParseError("ttest command: RHS must be a single variable name or a numeric value")


def _parse_recode(text: str) -> RecodeCommand:
  stripped = text.strip()
  if not stripped.startswith("recode"):
    raise ParseError("recode command must start with recode")

  body = stripped[6:].strip()
  if not body:
    raise ParseError("recode command: missing variable list and rules")

  tokens = _tokenize(body)

  # Find options by scanning for a top-level comma
  depth = 0
  comma_idx = -1
  for idx, token in enumerate(tokens):
    if token.text == "(":
      depth += 1
    elif token.text == ")":
      depth -= 1
    elif token.text == "," and depth == 0:
      comma_idx = idx
      break

  if comma_idx != -1:
    body_tokens = tokens[:comma_idx]
    opt_tokens = tokens[comma_idx + 1 :]
  else:
    body_tokens = tokens
    opt_tokens = ()

  # Parse options
  generate_variables: tuple[str, ...] | None = None
  replace = False
  if opt_tokens:
    options = _parse_options(opt_tokens)
    generate_vals = _single_tuple_option(options, "generate", "recode")
    replace_flag = "replace" in {opt.name for opt in options}
    _require_flag_options(options, "recode", {"replace"})

    unsupported = {opt.name for opt in options} - {"generate", "replace"}
    if unsupported:
      raise ParseError(f"recode unsupported option: {', '.join(sorted(unsupported))}")

    if generate_vals is not None and replace_flag:
      raise ParseError("recode command: cannot specify both generate() and replace")
    if generate_vals is None and not replace_flag:
      raise ParseError("recode command requires either generate() or replace option")

    if generate_vals is not None:
      generate_variables = generate_vals
    replace = replace_flag
  else:
    raise ParseError("recode command requires either generate() or replace option")

  # Find variables and rules
  first_paren_idx = -1
  for idx, token in enumerate(body_tokens):
    if token.text == "(":
      first_paren_idx = idx
      break

  if first_paren_idx == -1:
    raise ParseError("recode command: no rules specified")
  if first_paren_idx == 0:
    raise ParseError("recode command: no variables specified")

  var_tokens = body_tokens[:first_paren_idx]
  rule_tokens = body_tokens[first_paren_idx:]

  variables = []
  for tok in var_tokens:
    if tok.kind != "identifier":
      raise ParseError(f"invalid variable name in recode list: {tok.text}")
    variables.append(tok.text)
  variables = tuple(variables)

  # Parse rules
  rules = []
  i = 0
  while i < len(rule_tokens):
    if rule_tokens[i].text != "(":
      raise ParseError(f"expected '(' at start of rule, got: {rule_tokens[i].text}")

    # Matching parenthesis
    paren_depth = 1
    j = i + 1
    while j < len(rule_tokens) and paren_depth > 0:
      if rule_tokens[j].text == "(":
        paren_depth += 1
      elif rule_tokens[j].text == ")":
        paren_depth -= 1
      if paren_depth == 0:
        break
      j += 1

    if paren_depth > 0:
      raise ParseError("unterminated rule parenthesis")

    block_tokens = rule_tokens[i + 1 : j]

    eq_indices = [idx for idx, t in enumerate(block_tokens) if t.text == "="]
    if not eq_indices:
      raise ParseError("recode rule expects '=' between inputs and output")
    if len(eq_indices) > 1:
      raise ParseError("recode rule contains multiple '=' symbols")

    eq_idx = eq_indices[0]
    lhs_toks = block_tokens[:eq_idx]
    rhs_toks = block_tokens[eq_idx + 1 :]

    if not lhs_toks:
      raise ParseError("recode rule: missing inputs before '='")
    if not rhs_toks:
      raise ParseError("recode rule: missing output after '='")

    # LHS Pass 1: parsed primitives and slashes
    class _Slash:
      pass

    lhs_primitives = []
    k = 0
    while k < len(lhs_toks):
      tok = lhs_toks[k]
      if tok.text in {"-", "+"} and k + 1 < len(lhs_toks) and lhs_toks[k + 1].kind == "number":
        val = (
          float(lhs_toks[k + 1].text) if "." in lhs_toks[k + 1].text else int(lhs_toks[k + 1].text)
        )
        if tok.text == "-":
          val = -val
        lhs_primitives.append(val)
        k += 2
      elif tok.kind == "number":
        val = float(tok.text) if "." in tok.text else int(tok.text)
        lhs_primitives.append(val)
        k += 1
      elif tok.kind == "string":
        lhs_primitives.append(tok.text)
        k += 1
      elif tok.kind == "identifier":
        lhs_primitives.append(tok.text.lower())
        k += 1
      elif tok.text == "/":
        lhs_primitives.append(_Slash)
        k += 1
      else:
        raise ParseError(f"unexpected token in recode rule input: {tok.text}")

    # LHS Pass 2: parse RecodeRange and primitives
    inputs = []
    k = 0
    while k < len(lhs_primitives):
      if k + 1 < len(lhs_primitives) and lhs_primitives[k + 1] is _Slash:
        if k + 2 >= len(lhs_primitives):
          raise ParseError("unterminated range in recode rule")
        start = lhs_primitives[k]
        end = lhs_primitives[k + 2]
        if not (isinstance(start, (int, float)) or start == "min"):
          raise ParseError(f"invalid range start in recode rule: {start}")
        if not (isinstance(end, (int, float)) or end == "max"):
          raise ParseError(f"invalid range end in recode rule: {end}")
        inputs.append(RecodeRange(start=start, end=end))
        k += 3
      elif lhs_primitives[k] is _Slash:
        raise ParseError("invalid slash positioning in recode rule")
      else:
        val = lhs_primitives[k]
        if val in {"missing", "nonmissing", "else"}:
          inputs.append(val)
        else:
          inputs.append(val)
        k += 1

    if "else" in inputs and len(inputs) > 1:
      raise ParseError("else rule must not be combined with other inputs")

    # RHS: Parse output value
    rhs_primitives = []
    k = 0
    while k < len(rhs_toks):
      tok = rhs_toks[k]
      if tok.text in {"-", "+"} and k + 1 < len(rhs_toks) and rhs_toks[k + 1].kind == "number":
        val = (
          float(rhs_toks[k + 1].text) if "." in rhs_toks[k + 1].text else int(rhs_toks[k + 1].text)
        )
        if tok.text == "-":
          val = -val
        rhs_primitives.append(val)
        k += 2
      elif tok.kind == "number":
        val = float(tok.text) if "." in tok.text else int(tok.text)
        rhs_primitives.append(val)
        k += 1
      elif tok.kind == "string":
        rhs_primitives.append(tok.text)
        k += 1
      elif tok.kind == "identifier":
        rhs_primitives.append(tok.text.lower())
        k += 1
      else:
        raise ParseError(f"unexpected token in recode rule output: {tok.text}")

    if len(rhs_primitives) != 1:
      raise ParseError("recode rule output must be a single value")
    output_val = rhs_primitives[0]

    rules.append(RecodeRule(inputs=tuple(inputs), output=output_val))
    i = j + 1

  return RecodeCommand(
    variables=variables,
    rules=tuple(rules),
    generate_variables=generate_variables,
    replace=replace,
  )

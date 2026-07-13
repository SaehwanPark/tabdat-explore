"""Command-line entry point for TabDat."""

import argparse
import os
import platform
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import replace
from enum import Enum, auto
from pathlib import Path
from typing import Any, Literal, Protocol

from tabdat import __version__
from tabdat.config import TabDatConfig, load_config, load_default_config
from tabdat.errors import TabDatError
from tabdat.executor import Executor
from tabdat.formatter import format_error_json, format_result, format_result_json
from tabdat.help import available_help_topics, load_help_topic, load_help_topic_text
from tabdat.models import (
  EFFECT_CATEGORY_ORDER,
  ArgumentDescriptor,
  BarCommand,
  BayesPlotCommand,
  Command,
  CommandCatalogEntry,
  CommandCatalogResult,
  CommandEffectCatalogResult,
  CommandEffectEntry,
  CommandExplainResult,
  CommandSchemaResult,
  EffectCategory,
  ExitCommand,
  HelpCommand,
  HelpTopicResult,
  HistogramCommand,
  OptionDescriptor,
  PlotResult,
  Result,
  RunCommand,
  ScatterCommand,
)
from tabdat.parser import parse_command
from tabdat.script import (
  ElseDirective,
  EndDirective,
  IfDirective,
  LetDirective,
  ScriptBlockState,
  ScriptContext,
  ScriptError,
  SeedDirective,
  expand_script_macros,
  parse_control_flow_directive,
  parse_script_directive,
  read_script,
)
from tabdat.shell import COMMAND_NAMES, create_prompt_session
from tabdat.visualization import next_available_plot_path


class _RunStatus(Enum):
  CONTINUE = auto()
  STOP = auto()
  ERROR = auto()


OutputFormat = Literal["terminal", "json"]

_EFFECT_CATEGORY_RANK = {category: index for index, category in enumerate(EFFECT_CATEGORY_ORDER)}
_COMMAND_EFFECTS: dict[str, tuple[EffectCategory, ...]] = {
  "append": ("read", "write"),
  "bar": ("read", "plot"),
  "bayes": ("read",),
  "bayesplot": ("read", "plot"),
  "by": ("read", "write", "control", "plot"),
  "cfregress": ("read",),
  "codebook": ("read",),
  "collapse": ("read", "write"),
  "count": ("read",),
  "cvelasticnet": ("read", "write"),
  "cvlasso": ("read", "write"),
  "cvridge": ("read", "write"),
  "describe": ("read",),
  "did": ("read",),
  "dml": ("read",),
  "drdid": ("read",),
  "drop": ("read", "write"),
  "elasticnet": ("read",),
  "estat": ("read", "plot"),
  "exit": ("control",),
  "export": ("read", "write"),
  "generate": ("read", "write"),
  "head": ("read",),
  "heckman": ("read",),
  "help": ("control",),
  "histogram": ("read", "plot"),
  "ivregress": ("read",),
  "join": ("read", "write"),
  "keep": ("read", "write"),
  "lasso": ("read",),
  "lincom": ("read",),
  "logit": ("read",),
  "lowess": ("read", "write"),
  "nbreg": ("read",),
  "nl": ("read",),
  "panel": ("control",),
  "poisson": ("read",),
  "postlasso": ("read",),
  "predict": ("read", "write"),
  "probit": ("read",),
  "qreg": ("read",),
  "quit": ("control",),
  "recode": ("read", "write"),
  "regress": ("read",),
  "rename": ("read", "write"),
  "replace": ("read", "write"),
  "reshape": ("read", "write"),
  "ridge": ("read",),
  "run": ("read", "write", "control", "plot"),
  "save": ("read", "write"),
  "scatter": ("read", "plot"),
  "select": ("read", "write"),
  "set": ("control",),
  "spregress": ("read",),
  "sql": ("read", "write"),
  "status": ("read",),
  "streg": ("read",),
  "summarize": ("read",),
  "tabulate": ("read",),
  "tail": ("read",),
  "test": ("read",),
  "tobit": ("read",),
  "ttest": ("read",),
  "use": ("read", "control"),
  "xtabond": ("read",),
  "xtdata": ("read", "write"),
  "xtlogit": ("read",),
  "xtreg": ("read",),
  "zinb": ("read",),
  "zip": ("read",),
}


_COMMAND_SCHEMAS: dict[str, CommandSchemaResult] = {
  "use": CommandSchemaResult(
    name="use",
    syntax="use <path>",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="path", required=True),),
    options=(
      OptionDescriptor(name="lazy", required=False),
      OptionDescriptor(name="engine", required=False),
      OptionDescriptor(name="delimiter", required=False),
      OptionDescriptor(name="has_header", required=False),
    ),
  ),
  "recode": CommandSchemaResult(
    name="recode",
    syntax="recode varname (rules) [, generate(newvar)]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="variable", required=True),
      ArgumentDescriptor(name="rules", required=True),
    ),
    options=(OptionDescriptor(name="generate", required=False),),
  ),
  "help": CommandSchemaResult(
    name="help",
    syntax="help [topic]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="topic", required=False),),
    options=(),
  ),
  "describe": CommandSchemaResult(
    name="describe",
    syntax="describe",
    help_topic=None,
    arguments=(),
    options=(),
  ),
  "status": CommandSchemaResult(
    name="status",
    syntax="status",
    help_topic=None,
    arguments=(),
    options=(),
  ),
  "summarize": CommandSchemaResult(
    name="summarize",
    syntax="summarize [varlist]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variables", required=False),),
    options=(),
  ),
  "codebook": CommandSchemaResult(
    name="codebook",
    syntax="codebook [varlist]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variables", required=False),),
    options=(),
  ),
  "count": CommandSchemaResult(
    name="count",
    syntax="count",
    help_topic=None,
    arguments=(),
    options=(),
  ),
  "head": CommandSchemaResult(
    name="head",
    syntax="head [N]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="n", required=False),),
    options=(),
  ),
  "tail": CommandSchemaResult(
    name="tail",
    syntax="tail [N]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="n", required=False),),
    options=(),
  ),
  "keep": CommandSchemaResult(
    name="keep",
    syntax="keep varlist",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variables", required=True),),
    options=(),
  ),
  "drop": CommandSchemaResult(
    name="drop",
    syntax="drop varlist",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variables", required=True),),
    options=(),
  ),
  "select": CommandSchemaResult(
    name="select",
    syntax="select varlist",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variables", required=True),),
    options=(),
  ),
  "rename": CommandSchemaResult(
    name="rename",
    syntax="rename oldvar newvar",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="old_name", required=True),
      ArgumentDescriptor(name="new_name", required=True),
    ),
    options=(),
  ),
  "generate": CommandSchemaResult(
    name="generate",
    syntax="generate newvar = exp",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="variable", required=True),
      ArgumentDescriptor(name="expression", required=True),
    ),
    options=(),
  ),
  "replace": CommandSchemaResult(
    name="replace",
    syntax="replace oldvar = exp [if exp]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="variable", required=True),
      ArgumentDescriptor(name="expression", required=True),
    ),
    options=(OptionDescriptor(name="if", required=False),),
  ),
  "tabulate": CommandSchemaResult(
    name="tabulate",
    syntax="tabulate varname",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variable", required=True),),
    options=(
      OptionDescriptor(name="missing", required=False),
      OptionDescriptor(name="values", required=False),
      OptionDescriptor(name="stat", required=False),
    ),
  ),
  "collapse": CommandSchemaResult(
    name="collapse",
    syntax="collapse (stat) vars [, by(vars)]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="targets", required=True),),
    options=(OptionDescriptor(name="by", required=False),),
  ),
  "join": CommandSchemaResult(
    name="join",
    syntax="join tablename on keys",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="table", required=True),
      ArgumentDescriptor(name="keys", required=True),
    ),
    options=(
      OptionDescriptor(name="how", required=False),
      OptionDescriptor(name="suffix", required=False),
    ),
  ),
  "append": CommandSchemaResult(
    name="append",
    syntax="append tablename",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="table", required=True),),
    options=(),
  ),
  "reshape": CommandSchemaResult(
    name="reshape",
    syntax="reshape long|wide stub, i(vars) j(var)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="direction", required=True),
      ArgumentDescriptor(name="stub", required=True),
    ),
    options=(
      OptionDescriptor(name="i", required=True),
      OptionDescriptor(name="j", required=True),
    ),
  ),
  "panel": CommandSchemaResult(
    name="panel",
    syntax="panel id time",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="id_variable", required=True),
      ArgumentDescriptor(name="time_variable", required=False),
    ),
    options=(),
  ),
  "sql": CommandSchemaResult(
    name="sql",
    syntax="sql query",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="query", required=True),),
    options=(),
  ),
  "histogram": CommandSchemaResult(
    name="histogram",
    syntax="histogram varname",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variable", required=True),),
    options=(),
  ),
  "scatter": CommandSchemaResult(
    name="scatter",
    syntax="scatter yvar xvar",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="y_variable", required=True),
      ArgumentDescriptor(name="x_variable", required=True),
    ),
    options=(),
  ),
  "bar": CommandSchemaResult(
    name="bar",
    syntax="bar varname",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variable", required=True),),
    options=(),
  ),
  "bayesplot": CommandSchemaResult(
    name="bayesplot",
    syntax="bayesplot trace",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="subcommand", required=True),),
    options=(),
  ),
  "run": CommandSchemaResult(
    name="run",
    syntax="run filename",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="filename", required=True),),
    options=(),
  ),
  "set": CommandSchemaResult(
    name="set",
    syntax="set name value",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="name", required=True),
      ArgumentDescriptor(name="value", required=True),
    ),
    options=(),
  ),
  "save": CommandSchemaResult(
    name="save",
    syntax="save filename",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="filename", required=True),),
    options=(),
  ),
  "export": CommandSchemaResult(
    name="export",
    syntax="export filename",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="filename", required=True),),
    options=(),
  ),
  "regress": CommandSchemaResult(
    name="regress",
    syntax="regress y x1 x2 [, robust cluster(var) noconstant wls(var) gls(var)]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
      OptionDescriptor(name="wls", required=False),
      OptionDescriptor(name="gls", required=False),
    ),
  ),
  "predict": CommandSchemaResult(
    name="predict",
    syntax="predict newvar [, xb residuals probabilities]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variable", required=True),),
    options=(
      OptionDescriptor(name="xb", required=False),
      OptionDescriptor(name="residuals", required=False),
      OptionDescriptor(name="probabilities", required=False),
    ),
  ),
  "estat": CommandSchemaResult(
    name="estat",
    syntax="estat subcommand",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="subcommand", required=True),),
    options=(
      OptionDescriptor(name="saving", required=False),
      OptionDescriptor(name="noopen", required=False),
    ),
  ),
  "test": CommandSchemaResult(
    name="test",
    syntax="test spec",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="specification", required=True),),
    options=(),
  ),
  "lincom": CommandSchemaResult(
    name="lincom",
    syntax="lincom spec",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="specification", required=True),),
    options=(),
  ),
  "ttest": CommandSchemaResult(
    name="ttest",
    syntax="ttest varname [, by(var)]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variable", required=True),),
    options=(OptionDescriptor(name="by", required=False),),
  ),
  "by": CommandSchemaResult(
    name="by",
    syntax="by varlist: command",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="variables", required=True),
      ArgumentDescriptor(name="command", required=True),
    ),
    options=(),
  ),
  "exit": CommandSchemaResult(
    name="exit",
    syntax="exit",
    help_topic=None,
    arguments=(),
    options=(),
  ),
  "quit": CommandSchemaResult(
    name="quit",
    syntax="quit",
    help_topic=None,
    arguments=(),
    options=(),
  ),
  "lasso": CommandSchemaResult(
    name="lasso",
    syntax="lasso model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="alpha", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "postlasso": CommandSchemaResult(
    name="postlasso",
    syntax="postlasso model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="alpha", required=False),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "ridge": CommandSchemaResult(
    name="ridge",
    syntax="ridge model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="alpha", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "elasticnet": CommandSchemaResult(
    name="elasticnet",
    syntax="elasticnet model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="alpha", required=False),
      OptionDescriptor(name="l1_ratio", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "cvlasso": CommandSchemaResult(
    name="cvlasso",
    syntax="cvlasso model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="cv", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "cvridge": CommandSchemaResult(
    name="cvridge",
    syntax="cvridge model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="cv", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "cvelasticnet": CommandSchemaResult(
    name="cvelasticnet",
    syntax="cvelasticnet model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="cv", required=False),
      OptionDescriptor(name="l1_ratio", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "bayes": CommandSchemaResult(
    name="bayes",
    syntax="bayes model y x",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="model", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="n_iter", required=False),
      OptionDescriptor(name="tol", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "qreg": CommandSchemaResult(
    name="qreg",
    syntax="qreg y x [, quantile(val)]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="quantile", required=False),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "logit": CommandSchemaResult(
    name="logit",
    syntax="logit y x1 x2",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "probit": CommandSchemaResult(
    name="probit",
    syntax="probit y x1 x2",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "tobit": CommandSchemaResult(
    name="tobit",
    syntax="tobit y x1 x2 [, ll(val) ul(val)]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="ll", required=True),
      OptionDescriptor(name="ul", required=False),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "heckman": CommandSchemaResult(
    name="heckman",
    syntax="heckman y x1 x2, selectdep(var) select(vars)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="selectdep", required=True),
      OptionDescriptor(name="select", required=True),
    ),
  ),
  "nl": CommandSchemaResult(
    name="nl",
    syntax="nl formula, params(vars) start(vals)",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="formula", required=True),),
    options=(
      OptionDescriptor(name="params", required=True),
      OptionDescriptor(name="start", required=True),
    ),
  ),
  "poisson": CommandSchemaResult(
    name="poisson",
    syntax="poisson y x1 x2",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "nbreg": CommandSchemaResult(
    name="nbreg",
    syntax="nbreg y x1 x2",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "zip": CommandSchemaResult(
    name="zip",
    syntax="zip y x1 x2, inflate(vars)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="inflate", required=True),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "zinb": CommandSchemaResult(
    name="zinb",
    syntax="zinb y x1 x2, inflate(vars)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="inflate", required=True),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "streg": CommandSchemaResult(
    name="streg",
    syntax="streg time vars, failure(var) dist(name)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="time_variable", required=True),
      ArgumentDescriptor(name="variables", required=False),
    ),
    options=(
      OptionDescriptor(name="failure", required=True),
      OptionDescriptor(name="dist", required=True),
    ),
  ),
  "ivregress": CommandSchemaResult(
    name="ivregress",
    syntax="ivregress estimator y x, endog(vars) iv(vars)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="estimator", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="endog", required=True),
      OptionDescriptor(name="iv", required=True),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
      OptionDescriptor(name="noconstant", required=False),
    ),
  ),
  "xtreg": CommandSchemaResult(
    name="xtreg",
    syntax="xtreg y x [, fe re]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="fe", required=False),
      OptionDescriptor(name="re", required=False),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
    ),
  ),
  "xtdata": CommandSchemaResult(
    name="xtdata",
    syntax="xtdata varlist [, within between]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="variables", required=True),),
    options=(
      OptionDescriptor(name="within", required=False),
      OptionDescriptor(name="between", required=False),
    ),
  ),
  "xtlogit": CommandSchemaResult(
    name="xtlogit",
    syntax="xtlogit y x [, fe]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="fe", required=False),
      OptionDescriptor(name="robust", required=False),
      OptionDescriptor(name="cluster", required=False),
    ),
  ),
  "xtabond": CommandSchemaResult(
    name="xtabond",
    syntax="xtabond y x [, lags(n)]",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(OptionDescriptor(name="lags", required=False),),
  ),
  "lowess": CommandSchemaResult(
    name="lowess",
    syntax="lowess y x, gen(newvar)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="y_variable", required=True),
      ArgumentDescriptor(name="x_variable", required=True),
    ),
    options=(OptionDescriptor(name="gen", required=True),),
  ),
  "did": CommandSchemaResult(
    name="did",
    syntax="did y [, treat(var) post(var)]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="depvar", required=True),),
    options=(
      OptionDescriptor(name="treat", required=False),
      OptionDescriptor(name="post", required=False),
    ),
  ),
  "drdid": CommandSchemaResult(
    name="drdid",
    syntax="drdid y [, treat(var) post(var)]",
    help_topic=None,
    arguments=(ArgumentDescriptor(name="depvar", required=True),),
    options=(
      OptionDescriptor(name="treat", required=False),
      OptionDescriptor(name="post", required=False),
    ),
  ),
  "dml": CommandSchemaResult(
    name="dml",
    syntax="dml estimator y controls, treat(var)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="estimator", required=True),
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="controls", required=False),
    ),
    options=(OptionDescriptor(name="treat", required=True),),
  ),
  "cfregress": CommandSchemaResult(
    name="cfregress",
    syntax="cfregress y x, endog(vars) iv(vars)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="endog", required=True),
      OptionDescriptor(name="iv", required=True),
    ),
  ),
  "spregress": CommandSchemaResult(
    name="spregress",
    syntax="spregress y x, coord(lat lon)",
    help_topic=None,
    arguments=(
      ArgumentDescriptor(name="depvar", required=True),
      ArgumentDescriptor(name="indepvars", required=False),
    ),
    options=(
      OptionDescriptor(name="coord", required=False),
      OptionDescriptor(name="weights", required=False),
      OptionDescriptor(name="id", required=False),
      OptionDescriptor(name="contiguity", required=False),
      OptionDescriptor(name="knn", required=False),
      OptionDescriptor(name="model", required=False),
      OptionDescriptor(name="robust", required=False),
    ),
  ),
}


class _PromptSession(Protocol):
  def prompt(self, *args: Any, **kwargs: Any) -> str: ...


def main(argv: Sequence[str] | None = None) -> int:
  """The primary command-line entry point for TabDat.

  Parses system arguments, reads configuration files, instantiates the session
  executor, and dispatches to one of the execution modes: single commands, script files,
  or the interactive shell.

  Args:
    argv: Optional list of argument strings. Defaults to sys.argv[1:].

  Returns:
    An integer exit code (0 for success, non-zero for failure).
  """
  parser = argparse.ArgumentParser(prog="tabdat")
  parser.add_argument("-c", "--command", action="append", help="run a command and exit")
  parser.add_argument("-f", "--file", type=Path, help="run a TabDat script file and exit")
  parser.add_argument("--config", type=Path, help="load a TabDat TOML config file")
  parser.add_argument(
    "--json",
    action="store_true",
    help="emit versioned JSONL results for batch or script execution",
  )
  parser.add_argument(
    "--list-commands",
    action="store_true",
    help="emit the available command catalog; requires --json",
  )
  parser.add_argument(
    "--list-command-effects",
    action="store_true",
    help="emit declared command effects; requires --json",
  )
  parser.add_argument(
    "--help-topic",
    metavar="TOPIC",
    help="emit one packaged help topic; requires --json",
  )
  parser.add_argument(
    "--explain",
    action="store_true",
    help="parse one batch command without executing it; requires --json",
  )
  parser.add_argument(
    "--describe-command",
    metavar="COMMAND",
    help="emit one command's schema; requires --json",
  )
  parser.add_argument("script", nargs="?", type=Path, help="run a TabDat script file and exit")
  args = parser.parse_args(argv)

  if args.list_commands and not args.json:
    parser.error("--list-commands requires --json")
  if args.list_command_effects and not args.json:
    parser.error("--list-command-effects requires --json")
  if args.help_topic is not None and not args.json:
    parser.error("--help-topic requires --json")
  if args.explain and not args.json:
    parser.error("--explain requires --json")
  if args.describe_command is not None and not args.json:
    parser.error("--describe-command requires --json")
  if args.list_commands and (
    args.command
    or args.file is not None
    or args.script is not None
    or args.describe_command is not None
  ):
    parser.error("--list-commands cannot be combined with command, script, or describe execution")
  if args.list_command_effects and (
    args.command
    or args.file is not None
    or args.script is not None
    or args.list_commands
    or args.help_topic is not None
    or args.explain
    or args.describe_command is not None
  ):
    parser.error("--list-command-effects cannot be combined with another execution mode")
  if args.help_topic is not None and (
    args.command
    or args.file is not None
    or args.script is not None
    or args.list_commands
    or args.describe_command is not None
  ):
    parser.error(
      "--help-topic cannot be combined with command, script, "
      "command discovery, or describe execution"
    )
  if args.explain and (
    args.list_commands or args.help_topic is not None or args.describe_command is not None
  ):
    parser.error(
      "--explain cannot be combined with command discovery, "
      "help-topic retrieval, or describe execution"
    )
  if args.describe_command is not None and (
    args.command
    or args.file is not None
    or args.script is not None
    or args.list_commands
    or args.list_command_effects
    or args.help_topic is not None
    or args.explain
  ):
    parser.error("--describe-command cannot be combined with another execution mode")
  if args.explain and (args.file is not None or args.script is not None):
    parser.error("--explain requires exactly one -c/--command")
  if args.explain and len(args.command or ()) != 1:
    parser.error("--explain requires exactly one -c/--command")
  if args.command and (args.file is not None or args.script is not None):
    parser.error("-c/--command cannot be combined with script execution")
  if args.file is not None and args.script is not None:
    parser.error("-f/--file cannot be combined with a positional script")
  script_path = args.file or args.script
  if args.json and not (
    args.command
    or script_path is not None
    or args.list_commands
    or args.list_command_effects
    or args.help_topic is not None
    or args.explain
    or args.describe_command is not None
  ):
    parser.error(
      "--json requires a command execution, script path, explain, or discovery/describe flag"
    )
  if args.list_commands:
    print(format_result_json(_command_catalog_result()))
    return 0
  if args.list_command_effects:
    print(format_result_json(_command_effect_catalog_result()))
    return 0
  if args.describe_command is not None:
    return _run_describe_command_json(args.describe_command)
  if args.help_topic is not None:
    return _run_help_topic_json(args.help_topic)
  if args.explain:
    return _run_explain_json(args.command[0])

  try:
    config = load_config(args.config) if args.config is not None else load_default_config()
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    return 1

  executor = Executor(config=config)
  try:
    if args.command:
      return _run_commands(
        args.command,
        executor,
        output_format="json" if args.json else "terminal",
      )
    if script_path is not None:
      return _run_script(
        script_path,
        executor,
        output_format="json" if args.json else "terminal",
      )
    return _run_shell(executor)
  finally:
    executor.close()


def _command_catalog_result() -> CommandCatalogResult:
  help_topics = set(available_help_topics())
  return CommandCatalogResult(
    commands=tuple(
      CommandCatalogEntry(name=name, help_topic=name if name in help_topics else None)
      for name in sorted(COMMAND_NAMES)
    )
  )


def _command_effect_catalog_result() -> CommandEffectCatalogResult:
  commands = tuple(
    CommandEffectEntry(
      name=name,
      effects=tuple(
        sorted(
          _COMMAND_EFFECTS.get(name, ("unknown",)),
          key=_EFFECT_CATEGORY_RANK.__getitem__,
        )
      ),
    )
    for name in sorted(COMMAND_NAMES)
  )
  return CommandEffectCatalogResult(commands=commands)


def _run_describe_command_json(name: str) -> int:
  try:
    result = _describe_command_result(name)
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    print(format_error_json(exc))
    return 1
  print(format_result_json(result))
  return 0


def _describe_command_result(name: str) -> CommandSchemaResult:
  normalized = name.strip().lower()
  if not normalized:
    raise TabDatError("command name cannot be empty")
  if normalized not in COMMAND_NAMES:
    raise TabDatError(f"unknown command name: {normalized}")

  help_topics = set(available_help_topics())
  schema_data = _COMMAND_SCHEMAS.get(normalized)
  if schema_data is None:
    schema_data = CommandSchemaResult(
      name=normalized,
      syntax=normalized,
      help_topic=normalized if normalized in help_topics else None,
      arguments=(),
      options=(),
    )
  else:
    schema_data = replace(
      schema_data,
      help_topic=normalized if normalized in help_topics else None,
    )
  return schema_data


def _run_help_topic_json(topic: str) -> int:
  try:
    result = _help_topic_result(topic)
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    print(format_error_json(exc))
    return 1
  print(format_result_json(result))
  return 0


def _help_topic_result(topic: str) -> HelpTopicResult:
  normalized = topic.strip().lower()
  if not normalized:
    raise TabDatError("help topic cannot be empty")
  try:
    if normalized not in set(available_help_topics()):
      raise TabDatError(f"unknown help topic: {normalized}")
    text = load_help_topic_text(normalized)
  except KeyError:
    raise TabDatError(f"unknown help topic: {normalized}") from None
  except (OSError, UnicodeError):
    raise TabDatError(f"unable to load help topic: {normalized}") from None
  return HelpTopicResult(help_topic=normalized, text=text)


def _run_explain_json(command_text: str) -> int:
  try:
    result = _command_explain_result(command_text)
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    print(format_error_json(exc))
    return 1
  print(format_result_json(result))
  return 0


def _command_explain_result(command_text: str) -> CommandExplainResult:
  parse_command(command_text)
  return CommandExplainResult(command_name=_preview_command_name(command_text), execution="not_run")


def _preview_command_name(command_text: str) -> str:
  first_token = command_text.strip().split(maxsplit=1)[0].lower()
  if first_token == "?":
    return "help"
  return first_token.rstrip(",:")


def _run_commands(
  commands: Sequence[str],
  executor: Executor,
  *,
  output_format: OutputFormat = "terminal",
) -> int:
  """Execute a list of commands sequentially and exit.

  This mode handles commands passed using the `-c` or `--command` command-line options.
  Execution stops early if any command encounters an error.

  Args:
    commands: Sequence of command strings to run.
    executor: The active Executor instance.

  Returns:
    Exit code 0 if all commands succeeded, or 1 if any command failed.
  """
  for command_text in commands:
    status = _run_one(
      command_text,
      executor,
      open_plots=False,
      output_format=output_format,
      help_chooser=None,
      run_script=lambda path: _run_script_status(
        path,
        executor,
        base_dir=None,
        active_stack=(),
        context=ScriptContext.empty(),
        output_format=output_format,
      ),
    )
    if status is _RunStatus.ERROR:
      return 1
    if status is _RunStatus.STOP:
      break
  return 0


def _run_shell(executor: Executor) -> int:
  """Run the interactive prompt-toolkit shell.

  Loops indefinitely, requesting input from the user, handling Ctrl+C, EOF,
  and executing commands via `_run_one`.

  Args:
    executor: The active Executor instance.

  Returns:
    Exit code 0 when the shell is exited cleanly.
  """
  session = create_prompt_session(executor)
  while True:
    try:
      command_text = session.prompt("tabdat> ")
      command_text = _read_multiline_sql(command_text, session.prompt)
    except KeyboardInterrupt:
      print()
      continue
    except EOFError:
      print()
      return 0

    status = _run_one(
      command_text,
      executor,
      open_plots=executor.state.config.graph_open,
      command_rewriter=_prepare_interactive_command,
      help_chooser=lambda topics: _prompt_for_help_topic(session, topics),
      run_script=lambda path: _run_script_status(
        path,
        executor,
        base_dir=None,
        active_stack=(),
        context=ScriptContext.empty(),
      ),
    )
    if status is _RunStatus.STOP:
      return 0


def _run_one(
  command_text: str,
  executor: Executor,
  *,
  open_plots: bool,
  output_format: OutputFormat = "terminal",
  command_rewriter: Callable[[Command, Executor], Command] | None = None,
  help_chooser: Callable[[tuple[str, ...]], str | None] | None = None,
  opener: Callable[[PlotResult], None] | None = None,
  run_script: Callable[[Path], _RunStatus] | None = None,
) -> _RunStatus:
  """Run a single command string and handle output, error catching, and plotting.

  Args:
    command_text: The raw command line input to parse and execute.
    executor: The active session Executor.
    open_plots: Whether plots generated by this command should be opened.
    command_rewriter: Optional callable to adjust/decorate commands (e.g., auto-save plots).
    help_chooser: Callable to prompt the user to choose a help topic if multiple match.
    opener: Callable to launch visualizers for plot results.
    run_script: Callable to handle run nested script commands.

  Returns:
    The running status outcome (CONTINUE, STOP, or ERROR).
  """
  try:
    status, result = _execute_one(
      command_text,
      executor,
      output_format=output_format,
      command_rewriter=command_rewriter,
      help_chooser=help_chooser,
      run_script=run_script,
    )
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    if output_format == "json":
      print(format_error_json(exc))
    return _RunStatus.ERROR

  if status is not _RunStatus.CONTINUE:
    return status
  if result is not None:
    formatted = format_result_json(result) if output_format == "json" else format_result(result)
    print(formatted)
    _open_plot_if_needed(result, open_plots=open_plots, opener=opener or _open_plot)
  return _RunStatus.CONTINUE


def _execute_one(
  command_text: str,
  executor: Executor,
  *,
  output_format: OutputFormat = "terminal",
  command_rewriter: Callable[[Command, Executor], Command] | None,
  help_chooser: Callable[[tuple[str, ...]], str | None] | None,
  run_script: Callable[[Path], _RunStatus] | None,
) -> tuple[_RunStatus, Result | None]:
  """Parse and dispatch a single command line to the executor or built-in handlers.

  Deals with command re-writing, and intercepts specific command types like
  HelpCommand, ExitCommand, and RunCommand that require direct CLI handler integration.

  Args:
    command_text: Raw command string.
    executor: The session Executor.
    command_rewriter: Optional hook to rewrite commands prior to execution.
    help_chooser: Interactive prompt callback for ambiguous help topics.
    run_script: Callback to run a script file.

  Returns:
    A tuple of the running status and the optional execution Result.

  Raises:
    TabDatError: For parser, semantic, or execution exceptions.
  """
  command = parse_command(command_text)
  if command_rewriter is not None:
    command = command_rewriter(command, executor)
  if isinstance(command, HelpCommand):
    if output_format == "json":
      raise TabDatError("help is not available with --json")
    topic = command.topic
    if topic is None:
      if help_chooser is None:
        raise TabDatError("help requires a command name outside the interactive shell")
      topic = help_chooser(available_help_topics())
      if topic is None:
        return _RunStatus.CONTINUE, None
    _print_help_topic(topic)
    return _RunStatus.CONTINUE, None
  if isinstance(command, ExitCommand):
    return _RunStatus.STOP, None
  if isinstance(command, RunCommand):
    if run_script is None:
      raise TabDatError("run is only available from the CLI")
    return run_script(command.path), None
  return _RunStatus.CONTINUE, executor.execute(command)


def _prompt_for_help_topic(session: _PromptSession, topics: tuple[str, ...]) -> str | None:
  if not topics:
    print("Error: no help topics are available", file=sys.stderr)
    return None

  print("Available help topics:")
  for index, topic in enumerate(topics, start=1):
    print(f"  {index}. {topic}")

  while True:
    try:
      choice = session.prompt("help> ")
    except KeyboardInterrupt:
      print()
      return None
    except EOFError:
      print()
      return None

    selected = _resolve_help_topic_choice(choice, topics)
    if selected is not None:
      return selected
    if not choice.strip():
      return None
    print(f"Error: unknown help topic: {choice}", file=sys.stderr)


def _resolve_help_topic_choice(choice: str, topics: tuple[str, ...]) -> str | None:
  stripped = choice.strip().lower()
  if not stripped:
    return None
  if stripped.isdigit():
    index = int(stripped)
    if 1 <= index <= len(topics):
      return topics[index - 1]
    return None
  if stripped in topics:
    return stripped
  return None


def _print_help_topic(topic: str) -> None:
  try:
    print(load_help_topic(topic))
  except KeyError as exc:
    raise TabDatError(f"unknown help topic: {topic}") from exc


def _prepare_interactive_command(command: Command, executor: Executor) -> Command:
  if isinstance(command, HistogramCommand) and command.saving is None:
    saving = next_available_plot_path(executor._default_plot_path("histogram", (command.variable,)))
    return replace(command, saving=saving)
  if isinstance(command, ScatterCommand) and command.saving is None:
    saving = next_available_plot_path(
      executor._default_plot_path("scatter", (command.y_variable, command.x_variable))
    )
    return replace(command, saving=saving)
  if isinstance(command, BarCommand) and command.saving is None:
    saving = next_available_plot_path(executor._default_plot_path("bar", (command.variable,)))
    return replace(command, saving=saving)
  if isinstance(command, BayesPlotCommand) and command.saving is None:
    saving = next_available_plot_path(executor._default_plot_path("bayesplot", (command.kind,)))
    return replace(command, saving=saving)
  return command


def _run_script(
  path: Path,
  executor: Executor,
  *,
  output_format: OutputFormat = "terminal",
  base_dir: Path | None = None,
  active_stack: tuple[Path, ...] = (),
) -> int:
  try:
    status = _run_script_status(
      path,
      executor,
      base_dir=base_dir,
      active_stack=active_stack,
      context=ScriptContext.empty(),
      output_format=output_format,
    )
  except ScriptError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    if output_format == "json":
      print(format_error_json(exc))
    return 1
  return 1 if status is _RunStatus.ERROR else 0


def _run_script_status(
  path: Path,
  executor: Executor,
  *,
  base_dir: Path | None,
  active_stack: tuple[Path, ...],
  context: ScriptContext,
  output_format: OutputFormat = "terminal",
) -> _RunStatus:
  resolved_path = _resolve_script_path(path, base_dir)
  if resolved_path in active_stack:
    raise ScriptError(resolved_path, 1, "recursive script inclusion is not supported")

  commands = read_script(resolved_path)
  if output_format == "terminal":
    _print_script_metadata(resolved_path, executor.state.config, context)
  next_stack = active_stack + (resolved_path,)
  block_state: ScriptBlockState | None = None

  for script_command in commands:
    if block_state is not None and not block_state.current_branch_active:
      stripped = script_command.text.strip()
      command_name = stripped.split(maxsplit=1)[0].lower() if stripped else ""
      if command_name not in {"if", "else", "end"}:
        continue

    try:
      expanded_text = expand_script_macros(
        script_command.text,
        context,
        path=resolved_path,
        line=script_command.start_line,
      )
    except ScriptError:
      raise

    control_directive = parse_control_flow_directive(
      expanded_text,
      path=resolved_path,
      line=script_command.start_line,
    )
    if isinstance(control_directive, IfDirective):
      if block_state is not None:
        raise ScriptError(
          resolved_path,
          script_command.start_line,
          "nested if blocks are not supported",
        )
      if output_format == "terminal":
        print(f". {expanded_text}")
      block_state = ScriptBlockState(
        start_line=script_command.start_line,
        condition_active=control_directive.active,
      )
      continue
    if isinstance(control_directive, ElseDirective):
      if block_state is None:
        raise ScriptError(resolved_path, script_command.start_line, "else without matching if")
      if block_state.in_else:
        raise ScriptError(
          resolved_path,
          script_command.start_line,
          "if block already has an else branch",
        )
      if output_format == "terminal":
        print(f". {expanded_text}")
      block_state = ScriptBlockState(
        start_line=block_state.start_line,
        condition_active=block_state.condition_active,
        in_else=True,
      )
      continue
    if isinstance(control_directive, EndDirective):
      if block_state is None:
        raise ScriptError(resolved_path, script_command.start_line, "end without matching if")
      if output_format == "terminal":
        print(f". {expanded_text}")
      block_state = None
      continue

    if output_format == "terminal":
      print(f". {expanded_text}")

    directive = parse_script_directive(
      expanded_text,
      context,
      path=resolved_path,
      line=script_command.start_line,
    )
    if isinstance(directive, SeedDirective):
      context.seed = directive.value
      if output_format == "terminal":
        print(f"Seed: {directive.value}")
      continue
    if isinstance(directive, LetDirective):
      context.macros[directive.name] = directive.value
      if output_format == "terminal":
        print(f"Macro set: {directive.name}")
      continue

    def run_nested(nested_path: Path) -> _RunStatus:
      return _run_script_status(
        nested_path,
        executor,
        base_dir=resolved_path.parent,
        active_stack=next_stack,
        context=context,
        output_format=output_format,
      )

    try:
      status, result = _execute_one(
        expanded_text,
        executor,
        output_format=output_format,
        command_rewriter=None,
        help_chooser=None,
        run_script=run_nested,
      )
      if result is not None:
        formatted = format_result_json(result) if output_format == "json" else format_result(result)
        print(formatted)
    except ScriptError:
      raise
    except TabDatError as exc:
      raise ScriptError(resolved_path, script_command.start_line, str(exc)) from exc
    if status is _RunStatus.ERROR:
      raise ScriptError(resolved_path, script_command.start_line, "command failed")
    if status is _RunStatus.STOP:
      break

  if block_state is not None:
    raise ScriptError(resolved_path, block_state.start_line, "if block is missing end")

  return _RunStatus.CONTINUE


def _resolve_script_path(path: Path, base_dir: Path | None) -> Path:
  candidate = path if path.is_absolute() else (base_dir or Path.cwd()) / path
  return candidate.expanduser().resolve()


def _print_script_metadata(path: Path, config: TabDatConfig, context: ScriptContext) -> None:
  print(f"Script: {_display_script_path(path)}")
  print(f"TabDat: {__version__}")
  print(f"Python: {platform.python_version()}")
  print(f"Seed: {context.seed if context.seed is not None else 'none'}")
  print(
    "Config: "
    f"graph_format={config.graph_format}, "
    f"artifact_dir={config.artifact_dir}, "
    f"graph_open={'on' if config.graph_open else 'off'}"
  )


def _display_script_path(path: Path) -> str:
  try:
    return str(path.relative_to(Path.cwd()))
  except ValueError:
    return str(path)


def _open_plot_if_needed(
  result: Result,
  *,
  open_plots: bool,
  opener: Callable[[PlotResult], None],
) -> None:
  if isinstance(result, PlotResult) and open_plots and result.should_open:
    opener(result)


def _open_plot(result: PlotResult) -> None:
  try:
    _open_path(result.path)
  except OSError as exc:
    print(f"Warning: could not open plot: {exc}", file=sys.stderr)


def _open_path(path: object) -> None:
  if sys.platform == "win32":
    startfile = getattr(os, "startfile")
    startfile(path)
    return
  subprocess.Popen([_open_command_for_platform(sys.platform), str(path)])


def _open_command_for_platform(platform: str) -> str:
  if platform == "darwin":
    return "open"
  return "xdg-open"


def _read_multiline_sql(
  command_text: str,
  read_continuation: Callable[[str], str] = input,
) -> str:
  if not _has_open_sql_triple_quote(command_text):
    return command_text

  lines = [command_text]
  while True:
    continuation = read_continuation("... ")
    lines.append(continuation)
    joined = "\n".join(lines)
    if not _has_open_sql_triple_quote(joined):
      return joined


def _has_open_sql_triple_quote(command_text: str) -> bool:
  stripped = command_text.lstrip()
  parts = stripped.split(maxsplit=1)
  return (
    len(parts) == 2
    and parts[0].lower() == "sql"
    and parts[1].lstrip().startswith('"""')
    and stripped.count('"""') % 2 == 1
  )


if __name__ == "__main__":
  raise SystemExit(main())

"""prompt-toolkit shell helpers for TabDat."""

import re
from collections.abc import Callable, Iterable
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text.base import StyleAndTextTuples
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from tabdat.executor import Executor
from tabdat.help import available_help_topics
from tabdat.models import DatasetInfo

COMMAND_NAMES: tuple[str, ...] = (
  "use",
  "help",
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
  "predict",
  "estat",
  "by",
  "exit",
  "quit",
)
_BY_CHILD_COMMAND_NAMES = tuple(name for name in COMMAND_NAMES if name != "help")

_COLUMN_COMMANDS = {
  "summarize",
  "codebook",
  "keep",
  "drop",
  "select",
  "rename",
  "generate",
  "replace",
  "tabulate",
  "collapse",
  "histogram",
  "scatter",
  "bar",
  "reshape",
  "panel",
  "regress",
  "lasso",
  "postlasso",
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
  "ivregress",
  "xtreg",
  "xtdata",
  "xtlogit",
  "xtabond",
  "did",
  "drdid",
  "dml",
  "cfregress",
  "lowess",
  "spregress",
}
_TABULATE_OPTIONS = ("row", "col", "missing")
_COLLAPSE_OPTIONS = ("by(",)
_HISTOGRAM_OPTIONS = ("bins=", "saving(", "noopen")
_SCATTER_OPTIONS = ("saving(", "noopen")
_BAR_OPTIONS = ("saving(", "missing", "noopen")
_REGRESS_OPTIONS = ("robust", "cluster(", "noconstant", "wls(", "gls(")
_LASSO_OPTIONS = ("alpha(", "noconstant")
_POSTLASSO_OPTIONS = ("alpha(", "robust", "noconstant")
_CVLASSO_OPTIONS = ("cv(", "noconstant")
_CVRIDGE_OPTIONS = ("cv(", "noconstant")
_CVELASTICNET_OPTIONS = ("cv(", "l1_ratio(", "noconstant")
_BAYES_OPTIONS = ("n_iter(", "tol(", "noconstant")
_SPREGRESS_OPTIONS = ("coord(", "model(", "knn(", "robust", "weights(", "id(", "contiguity(")
_QREG_OPTIONS = ("quantile(", "robust", "noconstant")
_LOGIT_OPTIONS = ("robust", "cluster(", "noconstant")
_PROBIT_OPTIONS = ("robust", "cluster(", "noconstant")
_TOBIT_OPTIONS = ("ll(", "ul(", "robust", "cluster(", "noconstant")
_HECKMAN_OPTIONS = ("selectdep(", "select(", "robust", "cluster(", "noconstant")
_NL_OPTIONS = ("params(", "start(", "robust", "noconstant")
_POISSON_OPTIONS = ("robust", "cluster(", "noconstant")
_NBREG_OPTIONS = ("robust", "cluster(", "noconstant")
_ZIP_OPTIONS = ("inflate(", "robust", "cluster(", "noconstant")
_ZINB_OPTIONS = ("inflate(", "robust", "cluster(", "noconstant")
_STREG_OPTIONS = ("failure(", "dist(", "robust", "cluster(", "noconstant")
_IVREGRESS_OPTIONS = ("endog(", "iv(", "robust", "cluster(", "noconstant")
_XTREG_OPTIONS = ("fe", "re", "robust", "cluster(")
_XTDATA_OPTIONS = ("within", "between")
_XTLOGIT_OPTIONS = ("fe", "robust")
_XTABOND_OPTIONS = ("robust", "lags(", "instlag(")
_DID_OPTIONS = ("treat(", "post(", "robust")
_DRDID_OPTIONS = ("treat(", "post(", "method(", "robust", "bootstrap(", "seed(")
_DML_OPTIONS = ("treat(", "folds(", "alpha(", "robust", "seed(", "noconstant")
_CFREGRESS_OPTIONS = ("endog(", "iv(", "robust", "cluster(", "noconstant")
_LOWESS_OPTIONS = ("gen(", "bandwidth=")
_PREDICT_OPTIONS = ("xb", "residuals", "pr", "spatial_lag")
_ESTAT_SUBCOMMANDS = (
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
)
_SQL_SUGGESTIONS = ("select", "from active", "where", "group by", "order by", "into")
_KEYWORDS = {"by", "if", "into"}
_PREFIX_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$|by\($")
_STYLE = Style.from_dict(
  {
    "command": "bold #00aa88",
    "keyword": "bold #aa5a00",
    "string": "#0087d7",
    "number": "#875fd7",
    "operator": "#666666",
    "paren": "#666666",
  }
)
_TOKEN_PATTERN = re.compile(
  r"(?P<string>'[^']*'|\"[^\"]*\")"
  r"|(?P<number>\b\d+(?:\.\d+)?\b)"
  r"|(?P<operator>==|!=|<=|>=|[+\-*/=<>,:])"
  r"|(?P<paren>[()])"
  r"|(?P<word>[A-Za-z_][A-Za-z0-9_]*)"
  r"|(?P<space>\s+)"
  r"|(?P<other>.)"
)


class TabdatCompleter(Completer):
  """Context-aware completions for the interactive shell."""

  def __init__(self, executor: Executor) -> None:
    self._executor = executor

  def get_completions(
    self,
    document: Document,
    complete_event: CompleteEvent,
  ) -> Iterable[Completion]:
    text = document.text_before_cursor
    stripped = text.lstrip()
    word = _completion_prefix(text)

    if _is_first_token(text):
      yield from _matching_completions(COMMAND_NAMES, word)
      return

    command_name = stripped.split(maxsplit=1)[0].lower()
    if command_name in {"use", "join", "append"}:
      yield from _matching_completions(self._executor.state.tables.keys(), word)
      return

    if command_name == "sql":
      yield from _matching_completions(_SQL_SUGGESTIONS, word)
      return

    if command_name in {"help", "?"}:
      yield from _matching_completions(available_help_topics(), word)
      return

    if command_name == "estat":
      yield from _matching_completions(_ESTAT_SUBCOMMANDS, word)
      return

    if command_name == "by":
      yield from self._by_completions(stripped, word)
      return

    if (
      command_name == "bayes:"
      or command_name.startswith("bayes,")
      or (command_name == "bayes" and ":" in stripped)
    ):
      yield from self._bayes_prefix_completions(stripped, word)
      return

    if command_name in {
      "tabulate",
      "collapse",
      "histogram",
      "scatter",
      "bar",
      "regress",
      "lasso",
      "postlasso",
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
      "ivregress",
      "xtreg",
      "xtdata",
      "xtlogit",
      "xtabond",
      "did",
      "drdid",
      "dml",
      "cfregress",
      "lowess",
      "predict",
    } and _is_after_comma(text):
      yield from _option_completions(command_name, word)
      return

    if command_name in _COLUMN_COMMANDS:
      yield from _matching_completions(_column_names(self._executor.state.active_dataset), word)

  def _by_completions(self, stripped: str, word: str) -> Iterable[Completion]:
    before_colon, separator, after_colon = stripped.partition(":")
    if not separator:
      yield from _matching_completions(
        _column_names(self._executor.state.active_dataset),
        word,
      )
      return

    if _is_first_token(after_colon):
      yield from _matching_completions(_BY_CHILD_COMMAND_NAMES, word)
      return

    child_name = after_colon.strip().split(maxsplit=1)[0].lower()
    if child_name in _COLUMN_COMMANDS:
      yield from _matching_completions(
        _column_names(self._executor.state.active_dataset),
        word,
      )

  def _bayes_prefix_completions(self, stripped: str, word: str) -> Iterable[Completion]:
    before_colon, separator, after_colon = stripped.partition(":")
    if not separator:
      if "," in before_colon:
        mcmc_options = (
          "draws(",
          "burnin(",
          "tune(",
          "chains(",
          "thin(",
          "seed(",
          "rseed(",
          "prior(",
        )
        yield from _matching_completions(mcmc_options, word)
      return

    if _is_first_token(after_colon):
      yield from _matching_completions(("regress", "logit"), word)
      return

    child_name = after_colon.strip().split(maxsplit=1)[0].lower()
    if child_name in ("regress", "logit") and _is_after_comma(after_colon):
      yield from _option_completions(child_name, word)
      return

    yield from _matching_completions(
      _column_names(self._executor.state.active_dataset),
      word,
    )


class TabdatLexer(Lexer):
  """Lightweight command syntax highlighting."""

  def lex_document(self, document: Document) -> Callable[[int], StyleAndTextTuples]:
    lines = document.lines

    def get_line(lineno: int) -> StyleAndTextTuples:
      return _highlight_line(lines[lineno])

    return get_line


def create_prompt_session(
  executor: Executor,
  *,
  history: History | None = None,
) -> PromptSession[str]:
  return PromptSession(
    history=history or FileHistory(str(_history_path())),
    completer=TabdatCompleter(executor),
    lexer=TabdatLexer(),
    auto_suggest=AutoSuggestFromHistory(),
    style=_STYLE,
  )


def _history_path() -> Path:
  return Path.home() / ".tabdat_history"


def _is_first_token(text: str) -> bool:
  stripped = text.lstrip()
  return not stripped or not any(character.isspace() for character in stripped)


def _completion_prefix(text: str) -> str:
  match = _PREFIX_PATTERN.search(text)
  if match is None:
    return ""
  return match.group(0)


def _is_after_comma(text: str) -> bool:
  return "," in text


def _option_completions(command_name: str, word: str) -> Iterable[Completion]:
  if command_name == "tabulate":
    yield from _matching_completions(_TABULATE_OPTIONS, word)
  if command_name == "collapse":
    yield from _matching_completions(_COLLAPSE_OPTIONS, word)
  if command_name == "histogram":
    yield from _matching_completions(_HISTOGRAM_OPTIONS, word)
  if command_name == "scatter":
    yield from _matching_completions(_SCATTER_OPTIONS, word)
  if command_name == "bar":
    yield from _matching_completions(_BAR_OPTIONS, word)
  if command_name == "regress":
    yield from _matching_completions(_REGRESS_OPTIONS, word)
  if command_name == "lasso":
    yield from _matching_completions(_LASSO_OPTIONS, word)
  if command_name == "postlasso":
    yield from _matching_completions(_POSTLASSO_OPTIONS, word)
  if command_name == "cvlasso":
    yield from _matching_completions(_CVLASSO_OPTIONS, word)
  if command_name == "cvridge":
    yield from _matching_completions(_CVRIDGE_OPTIONS, word)
  if command_name == "cvelasticnet":
    yield from _matching_completions(_CVELASTICNET_OPTIONS, word)
  if command_name == "bayes":
    yield from _matching_completions(_BAYES_OPTIONS, word)
  if command_name == "spregress":
    yield from _matching_completions(_SPREGRESS_OPTIONS, word)
  if command_name == "qreg":
    yield from _matching_completions(_QREG_OPTIONS, word)
  if command_name == "logit":
    yield from _matching_completions(_LOGIT_OPTIONS, word)
  if command_name == "probit":
    yield from _matching_completions(_PROBIT_OPTIONS, word)
  if command_name == "tobit":
    yield from _matching_completions(_TOBIT_OPTIONS, word)
  if command_name == "heckman":
    yield from _matching_completions(_HECKMAN_OPTIONS, word)
  if command_name == "nl":
    yield from _matching_completions(_NL_OPTIONS, word)
  if command_name == "poisson":
    yield from _matching_completions(_POISSON_OPTIONS, word)
  if command_name == "nbreg":
    yield from _matching_completions(_NBREG_OPTIONS, word)
  if command_name == "zip":
    yield from _matching_completions(_ZIP_OPTIONS, word)
  if command_name == "zinb":
    yield from _matching_completions(_ZINB_OPTIONS, word)
  if command_name == "streg":
    yield from _matching_completions(_STREG_OPTIONS, word)
  if command_name == "ivregress":
    yield from _matching_completions(_IVREGRESS_OPTIONS, word)
  if command_name == "xtreg":
    yield from _matching_completions(_XTREG_OPTIONS, word)
  if command_name == "xtdata":
    yield from _matching_completions(_XTDATA_OPTIONS, word)
  if command_name == "xtlogit":
    yield from _matching_completions(_XTLOGIT_OPTIONS, word)
  if command_name == "xtabond":
    yield from _matching_completions(_XTABOND_OPTIONS, word)
  if command_name == "lowess":
    yield from _matching_completions(_LOWESS_OPTIONS, word)
  if command_name == "did":
    yield from _matching_completions(_DID_OPTIONS, word)
  if command_name == "drdid":
    yield from _matching_completions(_DRDID_OPTIONS, word)
  if command_name == "dml":
    yield from _matching_completions(_DML_OPTIONS, word)
  if command_name == "cfregress":
    yield from _matching_completions(_CFREGRESS_OPTIONS, word)
  if command_name == "predict":
    yield from _matching_completions(_PREDICT_OPTIONS, word)


def _matching_completions(candidates: Iterable[str], word: str) -> Iterable[Completion]:
  normalized_word = word.lower()
  for candidate in candidates:
    if candidate.lower().startswith(normalized_word):
      yield Completion(candidate, start_position=-len(word))


def _column_names(dataset: DatasetInfo | None) -> tuple[str, ...]:
  if dataset is None:
    return ()
  return tuple(column.name for column in dataset.columns)


def _highlight_line(line: str) -> StyleAndTextTuples:
  fragments: StyleAndTextTuples = []
  first_word = True
  for match in _TOKEN_PATTERN.finditer(line):
    text = match.group(0)
    kind = match.lastgroup
    style = ""
    if kind == "word":
      normalized = text.lower()
      if first_word and normalized in COMMAND_NAMES:
        style = "class:command"
      elif normalized in _KEYWORDS:
        style = "class:keyword"
      first_word = False
    elif kind == "string":
      style = "class:string"
    elif kind == "number":
      style = "class:number"
    elif kind == "operator":
      style = "class:operator"
    elif kind == "paren":
      style = "class:paren"
    fragments.append((style, text))
  return fragments

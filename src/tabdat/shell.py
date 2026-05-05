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
from tabdat.models import DatasetInfo

COMMAND_NAMES: tuple[str, ...] = (
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
  "sql",
  "histogram",
  "scatter",
  "bar",
  "run",
  "by",
  "exit",
  "quit",
)

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
}
_TABULATE_OPTIONS = ("row", "col", "missing")
_COLLAPSE_OPTIONS = ("by(",)
_HISTOGRAM_OPTIONS = ("bins=", "saving(", "noopen")
_SCATTER_OPTIONS = ("saving(", "noopen")
_BAR_OPTIONS = ("saving(", "missing", "noopen")
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
    if command_name == "sql":
      yield from _matching_completions(_SQL_SUGGESTIONS, word)
      return

    if command_name == "by":
      yield from self._by_completions(stripped, word)
      return

    if command_name in {"tabulate", "collapse", "histogram", "scatter", "bar"} and _is_after_comma(
      text
    ):
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
      yield from _matching_completions(COMMAND_NAMES, word)
      return

    child_name = after_colon.strip().split(maxsplit=1)[0].lower()
    if child_name in _COLUMN_COMMANDS:
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

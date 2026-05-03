from pathlib import Path

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.history import InMemoryHistory

from tabdat.executor import Executor
from tabdat.models import UseCommand
from tabdat.shell import TabdatCompleter, TabdatLexer, create_prompt_session


def _completion_texts(completer: TabdatCompleter, text: str) -> list[str]:
  return [
    completion.text
    for completion in completer.get_completions(
      Document(text, cursor_position=len(text)),
      CompleteEvent(),
    )
  ]


def test_completer_suggests_command_names() -> None:
  executor = Executor()
  try:
    completions = _completion_texts(TabdatCompleter(executor), "sum")
  finally:
    executor.close()

  assert completions == ["summarize"]


def test_completer_omits_columns_before_dataset_load() -> None:
  executor = Executor()
  try:
    completions = _completion_texts(TabdatCompleter(executor), "summarize ")
  finally:
    executor.close()

  assert completions == []


def test_completer_suggests_active_dataset_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completions = _completion_texts(TabdatCompleter(executor), "summarize b")
  finally:
    executor.close()

  assert completions == ["bmi"]


def test_completer_suggests_tabulate_options(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completions = _completion_texts(TabdatCompleter(executor), "tabulate sex, ")
  finally:
    executor.close()

  assert completions == ["row", "col", "missing"]


def test_completer_suggests_by_columns_and_child_commands(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    group_completions = _completion_texts(TabdatCompleter(executor), "by s")
    child_completions = _completion_texts(TabdatCompleter(executor), "by sex: sum")
  finally:
    executor.close()

  assert group_completions == ["sex"]
  assert child_completions == ["summarize"]


def test_completer_suggests_sql_helpers() -> None:
  executor = Executor()
  try:
    completions = _completion_texts(TabdatCompleter(executor), "sql group")
  finally:
    executor.close()

  assert completions == ["group by"]


def test_lexer_highlights_commands_keywords_and_literals() -> None:
  lexer = TabdatLexer()
  line = lexer.lex_document(Document("summarize age if age >= 42"))(0)

  assert ("class:command", "summarize") in line
  assert ("class:keyword", "if") in line
  assert ("class:operator", ">=") in line
  assert ("class:number", "42") in line


def test_prompt_session_uses_supplied_history() -> None:
  executor = Executor()
  try:
    session = create_prompt_session(executor, history=InMemoryHistory())
  finally:
    executor.close()

  assert isinstance(session.completer, TabdatCompleter)
  assert isinstance(session.lexer, TabdatLexer)

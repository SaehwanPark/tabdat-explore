from pathlib import Path

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.history import InMemoryHistory

from tabdat.executor import Executor
from tabdat.models import SqlCommand, UseCommand
from tabdat.shell import TabdatCompleter, TabdatLexer, create_prompt_session


def _completion_texts(completer: TabdatCompleter, text: str) -> list[str]:
  return [
    completion.text
    for completion in completer.get_completions(
      Document(text, cursor_position=len(text)),
      CompleteEvent(),
    )
  ]


def _completion_start_positions(completer: TabdatCompleter, text: str) -> list[int]:
  return [
    completion.start_position
    for completion in completer.get_completions(
      Document(text, cursor_position=len(text)),
      CompleteEvent(),
    )
  ]


def test_completer_suggests_command_names() -> None:
  executor = Executor()
  try:
    completions = _completion_texts(TabdatCompleter(executor), "sum")
    reshape_completions = _completion_texts(TabdatCompleter(executor), "resh")
    panel_completions = _completion_texts(TabdatCompleter(executor), "pan")
  finally:
    executor.close()

  assert completions == ["summarize"]
  assert reshape_completions == ["reshape"]
  assert panel_completions == ["panel"]


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
    panel_completions = _completion_texts(TabdatCompleter(executor), "panel s")
  finally:
    executor.close()

  assert completions == ["bmi"]
  assert panel_completions == ["sex"]


def test_completer_suggests_tabulate_options(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completions = _completion_texts(TabdatCompleter(executor), "tabulate sex, ")
  finally:
    executor.close()

  assert completions == ["row", "col", "missing"]


def test_completer_suggests_tabulate_options_after_compact_comma(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completer = TabdatCompleter(executor)
    all_options = _completion_texts(completer, "tabulate sex,")
    row_option = _completion_texts(completer, "tabulate sex,r")
    row_start_positions = _completion_start_positions(completer, "tabulate sex,r")
  finally:
    executor.close()

  assert all_options == ["row", "col", "missing"]
  assert row_option == ["row"]
  assert row_start_positions == [-1]


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


def test_completer_suggests_by_child_commands_after_compact_colon(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completer = TabdatCompleter(executor)
    all_commands = _completion_texts(completer, "by sex:")
    summarize_command = _completion_texts(completer, "by sex:sum")
    summarize_start_positions = _completion_start_positions(completer, "by sex:sum")
  finally:
    executor.close()

  assert "summarize" in all_commands
  assert summarize_command == ["summarize"]
  assert summarize_start_positions == [-3]


def test_completer_suggests_sql_helpers() -> None:
  executor = Executor()
  try:
    completions = _completion_texts(TabdatCompleter(executor), "sql group")
  finally:
    executor.close()

  assert completions == ["group by"]


def test_completer_suggests_named_tables_for_use(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(SqlCommand("select sex from active order by sex", into="summary"))
    completions = _completion_texts(TabdatCompleter(executor), "use s")
  finally:
    executor.close()

  assert completions == ["summary"]


def test_completer_suggests_visualization_columns_and_options(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completer = TabdatCompleter(executor)
    histogram_columns = _completion_texts(completer, "histogram a")
    histogram_options = _completion_texts(completer, "histogram age, ")
    scatter_options = _completion_texts(completer, "scatter bmi age, s")
    bar_options = _completion_texts(completer, "bar sex, m")
  finally:
    executor.close()

  assert histogram_columns == ["age"]
  assert histogram_options == ["bins=", "saving(", "noopen"]
  assert scatter_options == ["saving("]
  assert bar_options == ["missing"]


def test_completer_suggests_phase_13_commands_and_options(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completer = TabdatCompleter(executor)
    regress_command = _completion_texts(completer, "regr")
    regress_columns = _completion_texts(completer, "regress c")
    regress_options = _completion_texts(completer, "regress cost age, ")
    predict_command = _completion_texts(completer, "pred")
    predict_options = _completion_texts(completer, "predict cost_hat, ")
  finally:
    executor.close()

  assert regress_command == ["regress"]
  assert regress_columns == ["cost"]
  assert regress_options == ["robust", "cluster(", "noconstant"]
  assert predict_command == ["predict"]
  assert predict_options == ["xb", "residuals"]


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

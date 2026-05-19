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
    help_completions = _completion_texts(TabdatCompleter(executor), "hel")
  finally:
    executor.close()

  assert completions == ["summarize"]
  assert reshape_completions == ["reshape"]
  assert panel_completions == ["panel"]
  assert help_completions == ["help"]


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
    help_child_completions = _completion_texts(TabdatCompleter(executor), "by sex: help")
  finally:
    executor.close()

  assert group_completions == ["sex"]
  assert child_completions == ["summarize"]
  assert help_child_completions == []


def test_completer_suggests_help_topics() -> None:
  executor = Executor()
  try:
    completions = _completion_texts(TabdatCompleter(executor), "help summar")
  finally:
    executor.close()

  assert completions == ["summarize"]


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


def test_completer_suggests_phase_13_and_phase_14_commands_and_options(
  sample_parquet: Path,
) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    completer = TabdatCompleter(executor)
    regress_command = _completion_texts(completer, "regr")
    regress_columns = _completion_texts(completer, "regress c")
    regress_options = _completion_texts(completer, "regress cost age, ")
    qreg_command = _completion_texts(completer, "qre")
    qreg_columns = _completion_texts(completer, "qreg c")
    qreg_options = _completion_texts(completer, "qreg cost age, ")
    logit_command = _completion_texts(completer, "log")
    logit_columns = _completion_texts(completer, "logit c")
    logit_options = _completion_texts(completer, "logit cost age, ")
    probit_command = _completion_texts(completer, "prob")
    probit_columns = _completion_texts(completer, "probit c")
    probit_options = _completion_texts(completer, "probit cost age, ")
    tobit_command = _completion_texts(completer, "tob")
    tobit_columns = _completion_texts(completer, "tobit c")
    tobit_options = _completion_texts(completer, "tobit cost age, ")
    heckman_command = _completion_texts(completer, "heck")
    heckman_columns = _completion_texts(completer, "heckman c")
    heckman_options = _completion_texts(completer, "heckman cost age, ")
    nl_command = _completion_texts(completer, "nl")
    nl_columns = _completion_texts(completer, "nl c")
    nl_options = _completion_texts(completer, "nl cost = a + b * age, ")
    poisson_command = _completion_texts(completer, "pois")
    poisson_columns = _completion_texts(completer, "poisson c")
    poisson_options = _completion_texts(completer, "poisson cost age, ")
    nbreg_command = _completion_texts(completer, "nbr")
    nbreg_columns = _completion_texts(completer, "nbreg c")
    nbreg_options = _completion_texts(completer, "nbreg cost age, ")
    zip_command = _completion_texts(completer, "zi")
    zip_columns = _completion_texts(completer, "zip c")
    zip_options = _completion_texts(completer, "zip cost age, ")
    zinb_command = _completion_texts(completer, "zin")
    zinb_columns = _completion_texts(completer, "zinb c")
    zinb_options = _completion_texts(completer, "zinb cost age, ")
    streg_command = _completion_texts(completer, "str")
    streg_columns = _completion_texts(completer, "streg c")
    streg_options = _completion_texts(completer, "streg time age, ")
    ivregress_command = _completion_texts(completer, "ivr")
    ivregress_columns = _completion_texts(completer, "ivregress 2sls c")
    ivregress_gmm_columns = _completion_texts(completer, "ivregress gmm c")
    ivregress_options = _completion_texts(completer, "ivregress 2sls cost age, ")
    xtreg_command = _completion_texts(completer, "xtr")
    xtreg_columns = _completion_texts(completer, "xtreg c")
    xtreg_options = _completion_texts(completer, "xtreg cost age, ")
    xtdata_command = _completion_texts(completer, "xtd")
    xtdata_columns = _completion_texts(completer, "xtdata c")
    xtdata_options = _completion_texts(completer, "xtdata cost age, ")
    xtlogit_command = _completion_texts(completer, "xtl")
    xtlogit_columns = _completion_texts(completer, "xtlogit c")
    xtlogit_options = _completion_texts(completer, "xtlogit cost age, ")
    xtabond_command = _completion_texts(completer, "xta")
    xtabond_columns = _completion_texts(completer, "xtabond c")
    xtabond_options = _completion_texts(completer, "xtabond cost age, ")
    lowess_command = _completion_texts(completer, "low")
    lowess_columns = _completion_texts(completer, "lowess c")
    lowess_options = _completion_texts(completer, "lowess cost age, ")
    cfregress_command = _completion_texts(completer, "cfr")
    cfregress_columns = _completion_texts(completer, "cfregress c")
    cfregress_options = _completion_texts(completer, "cfregress cost age, ")
    did_command = _completion_texts(completer, "di")
    did_columns = _completion_texts(completer, "did c")
    did_options = _completion_texts(completer, "did cost age, ")
    predict_command = _completion_texts(completer, "pred")
    predict_options = _completion_texts(completer, "predict cost_hat, ")
    estat_command = _completion_texts(completer, "est")
    estat_subcommands = _completion_texts(completer, "estat o")
    estat_endogenous = _completion_texts(completer, "estat e")
    estat_margins = _completion_texts(completer, "estat m")
    estat_gof = _completion_texts(completer, "estat g")
  finally:
    executor.close()

  assert regress_command == ["regress"]
  assert regress_columns == ["cost"]
  assert regress_options == ["robust", "cluster(", "noconstant", "wls(", "gls("]
  assert qreg_command == ["qreg"]
  assert qreg_columns == ["cost"]
  assert qreg_options == ["quantile(", "robust", "noconstant"]
  assert logit_command == ["logit"]
  assert logit_columns == ["cost"]
  assert logit_options == ["robust", "cluster(", "noconstant"]
  assert probit_command == ["probit"]
  assert probit_columns == ["cost"]
  assert probit_options == ["robust", "cluster(", "noconstant"]
  assert tobit_command == ["tobit"]
  assert tobit_columns == ["cost"]
  assert tobit_options == ["ll(", "ul(", "robust", "cluster(", "noconstant"]
  assert heckman_command == ["heckman"]
  assert heckman_columns == ["cost"]
  assert heckman_options == ["selectdep(", "select(", "robust", "cluster(", "noconstant"]
  assert nl_command == ["nl"]
  assert nl_columns == ["cost"]
  assert nl_options == ["params(", "start(", "robust", "noconstant"]
  assert poisson_command == ["poisson"]
  assert poisson_columns == ["cost"]
  assert poisson_options == ["robust", "cluster(", "noconstant"]
  assert nbreg_command == ["nbreg"]
  assert nbreg_columns == ["cost"]
  assert nbreg_options == ["robust", "cluster(", "noconstant"]
  assert zip_command == ["zip", "zinb"]
  assert zip_columns == ["cost"]
  assert zip_options == ["inflate(", "robust", "cluster(", "noconstant"]
  assert zinb_command == ["zinb"]
  assert zinb_columns == ["cost"]
  assert zinb_options == ["inflate(", "robust", "cluster(", "noconstant"]
  assert streg_command == ["streg"]
  assert streg_columns == ["cost"]
  assert streg_options == ["failure(", "dist(", "robust", "cluster(", "noconstant"]
  assert ivregress_command == ["ivregress"]
  assert ivregress_columns == ["cost"]
  assert ivregress_gmm_columns == ["cost"]
  assert ivregress_options == ["endog(", "iv(", "robust", "cluster(", "noconstant"]
  assert xtreg_command == ["xtreg"]
  assert xtreg_columns == ["cost"]
  assert xtreg_options == ["fe", "re", "robust", "cluster("]
  assert xtdata_command == ["xtdata"]
  assert xtdata_columns == ["cost"]
  assert xtdata_options == ["within", "between"]
  assert xtlogit_command == ["xtlogit"]
  assert xtlogit_columns == ["cost"]
  assert xtlogit_options == ["fe", "robust"]
  assert xtabond_command == ["xtabond"]
  assert xtabond_columns == ["cost"]
  assert xtabond_options == ["robust", "lags(", "instlag("]
  assert lowess_command == ["lowess"]
  assert lowess_columns == ["cost"]
  assert lowess_options == ["gen(", "bandwidth="]
  assert cfregress_command == ["cfregress"]
  assert cfregress_columns == ["cost"]
  assert cfregress_options == ["endog(", "iv(", "robust", "cluster(", "noconstant"]
  assert did_command == ["did"]
  assert did_columns == ["cost"]
  assert did_options == ["treat(", "post(", "robust"]
  assert predict_command == ["predict"]
  assert predict_options == ["xb", "residuals", "pr"]
  assert estat_command == ["estat"]
  assert estat_subcommands == ["ovtest", "overid"]
  assert estat_endogenous == ["endogenous"]
  assert estat_gof == ["gof"]
  assert estat_margins == ["margins"]


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

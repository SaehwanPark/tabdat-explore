from tabdat.help import available_help_topics, load_help_topic
from tabdat.shell import COMMAND_NAMES


def test_help_topics_are_discoverable() -> None:
  topics = available_help_topics()

  assert "summarize" in topics
  assert "describe" in topics
  assert "status" in topics
  assert "lasso" in topics
  assert "postlasso" in topics
  assert "dml" in topics
  assert "bayesplot" in topics
  assert "ridge" in topics
  assert "elasticnet" in topics
  assert "poisson" in topics
  assert "nbreg" in topics
  assert "zip" in topics
  assert "zinb" in topics
  assert "streg" in topics
  assert "qreg" in topics
  assert "did" in topics
  assert "xtabond" in topics
  assert "xtlogit" in topics
  assert "lowess" in topics
  assert "help" not in topics


def test_help_topic_text_is_loaded_from_package_data() -> None:
  text = load_help_topic("summarize")

  assert "How to invoke" in text
  assert "What it does" in text
  assert "Examples" in text


def test_help_topics_document_explicit_missing_values() -> None:
  assert "cost == null" in load_help_topic("keep")
  assert "cost == null" in load_help_topic("drop")
  assert "generate missing_cost = null" in load_help_topic("generate")
  assert "cost != null" in load_help_topic("replace")
  assert "Division by zero" in load_help_topic("generate")
  assert "computed `inf` and `nan`" in load_help_topic("replace")
  assert "unsigned numeric variables" in load_help_topic("generate")
  assert "native ordering" in load_help_topic("tabulate")
  assert "descending count" in load_help_topic("bar")
  assert "explicit `order by`" in load_help_topic("sql")
  assert "tie-breaker keys" in load_help_topic("sql")
  assert "no row-order guarantee" in load_help_topic("sql")
  assert "restores its stored row sequence" in load_help_topic("use")


def test_help_topics_document_expression_domains() -> None:
  assert "numeric and string truthiness is rejected" in load_help_topic("keep")
  assert "prior relative order" in load_help_topic("keep")
  assert "prior relative order" in load_help_topic("drop")
  assert "head 0" in load_help_topic("head")
  assert "tail 0" in load_help_topic("tail")
  assert "Arithmetic requires numeric operands" in load_help_topic("generate")
  assert "numeric/string conversion is not" in load_help_topic("replace")
  assert "if` conditions must produce boolean or missing" in load_help_topic("tabulate")


def test_estat_help_mentions_bayes_diagnostics() -> None:
  text = load_help_topic("estat")

  assert "estat bayes" in text


def test_bayesplot_help_mentions_diagnostic_artifacts() -> None:
  text = load_help_topic("bayesplot")

  assert "bayesplot trace" in text
  assert "bayesplot density" in text
  assert "bayesplot autocorrelation" in text


def test_predict_help_mentions_bayes_posterior_intervals() -> None:
  text = load_help_topic("predict")

  assert "posterior_predictive interval" in text
  assert "level(<num>)" in text


def test_help_topics_cover_all_current_commands() -> None:
  topics = set(available_help_topics())
  optional = {"help", "by", "quit"}
  command_names = set(COMMAND_NAMES)
  missing = sorted(name for name in command_names if name not in topics and name not in optional)
  assert missing == []

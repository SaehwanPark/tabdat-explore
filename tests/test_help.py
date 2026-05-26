from tabdat.help import available_help_topics, load_help_topic
from tabdat.shell import COMMAND_NAMES


def test_help_topics_are_discoverable() -> None:
  topics = available_help_topics()

  assert "summarize" in topics
  assert "describe" in topics
  assert "lasso" in topics
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


def test_help_topics_cover_all_current_commands() -> None:
  topics = set(available_help_topics())
  optional = {"help", "by", "quit"}
  command_names = set(COMMAND_NAMES)
  missing = sorted(name for name in command_names if name not in topics and name not in optional)
  assert missing == []

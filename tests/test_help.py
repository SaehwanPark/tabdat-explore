from tabdat.help import available_help_topics, load_help_topic


def test_help_topics_are_discoverable() -> None:
  topics = available_help_topics()

  assert "summarize" in topics
  assert "describe" in topics
  assert "poisson" in topics
  assert "nbreg" in topics
  assert "zip" in topics
  assert "zinb" in topics
  assert "streg" in topics
  assert "help" not in topics


def test_help_topic_text_is_loaded_from_package_data() -> None:
  text = load_help_topic("summarize")

  assert "How to invoke" in text
  assert "What it does" in text
  assert "Examples" in text

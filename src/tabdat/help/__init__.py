"""Editable in-application help topics for TabDat."""

from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def available_help_topics() -> tuple[str, ...]:
  package = resources.files(__name__).joinpath("topics")
  topics = [
    candidate.name.removesuffix(".md")
    for candidate in package.iterdir()
    if candidate.is_file() and candidate.name.endswith(".md")
  ]
  return tuple(sorted(topics))


def load_help_topic(topic: str) -> str:
  package = resources.files(__name__).joinpath("topics")
  candidate = package.joinpath(f"{topic}.md")
  if not candidate.is_file():
    raise KeyError(topic)
  return candidate.read_text(encoding="utf-8").strip()

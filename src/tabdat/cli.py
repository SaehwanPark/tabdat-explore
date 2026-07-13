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
  BarCommand,
  BayesPlotCommand,
  Command,
  CommandCatalogEntry,
  CommandCatalogResult,
  CommandExplainResult,
  ExitCommand,
  HelpCommand,
  HelpTopicResult,
  HistogramCommand,
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
    "--help-topic",
    metavar="TOPIC",
    help="emit one packaged help topic; requires --json",
  )
  parser.add_argument(
    "--explain",
    action="store_true",
    help="parse one batch command without executing it; requires --json",
  )
  parser.add_argument("script", nargs="?", type=Path, help="run a TabDat script file and exit")
  args = parser.parse_args(argv)

  if args.list_commands and not args.json:
    parser.error("--list-commands requires --json")
  if args.help_topic is not None and not args.json:
    parser.error("--help-topic requires --json")
  if args.explain and not args.json:
    parser.error("--explain requires --json")
  if args.list_commands and (args.command or args.file is not None or args.script is not None):
    parser.error("--list-commands cannot be combined with command or script execution")
  if args.help_topic is not None and (
    args.command or args.file is not None or args.script is not None or args.list_commands
  ):
    parser.error("--help-topic cannot be combined with command, script, or command discovery")
  if args.explain and (args.list_commands or args.help_topic is not None):
    parser.error("--explain cannot be combined with command discovery or help-topic retrieval")
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
    or args.help_topic is not None
    or args.explain
  ):
    parser.error("--json requires -c/--command or a script path")
  if args.list_commands:
    print(format_result_json(_command_catalog_result()))
    return 0
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
  command = parse_command(command_text)
  return CommandExplainResult(command_type=type(command).__name__, execution="not_run")


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

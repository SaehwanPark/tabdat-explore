"""Command-line entry point for TabDat."""

import argparse
import os
import platform
import subprocess
import sys
from dataclasses import replace
from collections.abc import Callable, Sequence
from enum import Enum, auto
from pathlib import Path

from tabdat import __version__
from tabdat.config import TabDatConfig, load_config, load_default_config
from tabdat.errors import TabDatError
from tabdat.executor import Executor
from tabdat.formatter import format_result
from tabdat.models import (
  BarCommand,
  Command,
  ExitCommand,
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
from tabdat.shell import create_prompt_session
from tabdat.visualization import next_available_plot_path


class _RunStatus(Enum):
  CONTINUE = auto()
  STOP = auto()
  ERROR = auto()


def main(argv: Sequence[str] | None = None) -> int:
  parser = argparse.ArgumentParser(prog="tabdat")
  parser.add_argument("-c", "--command", action="append", help="run a command and exit")
  parser.add_argument("-f", "--file", type=Path, help="run a TabDat script file and exit")
  parser.add_argument("--config", type=Path, help="load a TabDat TOML config file")
  parser.add_argument("script", nargs="?", type=Path, help="run a TabDat script file and exit")
  args = parser.parse_args(argv)

  if args.command and (args.file is not None or args.script is not None):
    parser.error("-c/--command cannot be combined with script execution")
  if args.file is not None and args.script is not None:
    parser.error("-f/--file cannot be combined with a positional script")

  try:
    config = load_config(args.config) if args.config is not None else load_default_config()
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    return 1

  executor = Executor(config=config)
  try:
    if args.command:
      return _run_commands(args.command, executor)
    script_path = args.file or args.script
    if script_path is not None:
      return _run_script(script_path, executor)
    return _run_shell(executor)
  finally:
    executor.close()


def _run_commands(commands: Sequence[str], executor: Executor) -> int:
  for command_text in commands:
    status = _run_one(
      command_text,
      executor,
      open_plots=False,
      run_script=lambda path: _run_script_status(
        path,
        executor,
        base_dir=None,
        active_stack=(),
        context=ScriptContext.empty(),
      ),
    )
    if status is _RunStatus.ERROR:
      return 1
    if status is _RunStatus.STOP:
      break
  return 0


def _run_shell(executor: Executor) -> int:
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
  command_rewriter: Callable[[Command, Executor], Command] | None = None,
  opener: Callable[[PlotResult], None] | None = None,
  run_script: Callable[[Path], _RunStatus] | None = None,
) -> _RunStatus:
  try:
    status, result = _execute_one(
      command_text,
      executor,
      command_rewriter=command_rewriter,
      run_script=run_script,
    )
  except TabDatError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    return _RunStatus.ERROR

  if status is not _RunStatus.CONTINUE:
    return status
  if result is not None:
    print(format_result(result))
    _open_plot_if_needed(result, open_plots=open_plots, opener=opener or _open_plot)
  return _RunStatus.CONTINUE


def _execute_one(
  command_text: str,
  executor: Executor,
  *,
  command_rewriter: Callable[[Command, Executor], Command] | None,
  run_script: Callable[[Path], _RunStatus] | None,
) -> tuple[_RunStatus, Result | None]:
  command = parse_command(command_text)
  if command_rewriter is not None:
    command = command_rewriter(command, executor)
  if isinstance(command, ExitCommand):
    return _RunStatus.STOP, None
  if isinstance(command, RunCommand):
    if run_script is None:
      raise TabDatError("run is only available from the CLI")
    return run_script(command.path), None
  return _RunStatus.CONTINUE, executor.execute(command)


def _prepare_interactive_command(command: Command, executor: Executor) -> Command:
  if isinstance(command, HistogramCommand) and command.saving is None:
    saving = next_available_plot_path(
      executor._default_plot_path("histogram", (command.variable,))
    )
    return replace(command, saving=saving)
  if isinstance(command, ScatterCommand) and command.saving is None:
    saving = next_available_plot_path(
      executor._default_plot_path("scatter", (command.y_variable, command.x_variable))
    )
    return replace(command, saving=saving)
  if isinstance(command, BarCommand) and command.saving is None:
    saving = next_available_plot_path(
      executor._default_plot_path("bar", (command.variable,))
    )
    return replace(command, saving=saving)
  return command


def _run_script(
  path: Path,
  executor: Executor,
  *,
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
    )
  except ScriptError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    return 1
  return 1 if status is _RunStatus.ERROR else 0


def _run_script_status(
  path: Path,
  executor: Executor,
  *,
  base_dir: Path | None,
  active_stack: tuple[Path, ...],
  context: ScriptContext,
) -> _RunStatus:
  resolved_path = _resolve_script_path(path, base_dir)
  if resolved_path in active_stack:
    raise ScriptError(path, 1, "recursive script inclusion is not supported")

  commands = read_script(resolved_path)
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
      print(f". {expanded_text}")
      block_state = None
      continue

    print(f". {expanded_text}")

    directive = parse_script_directive(
      expanded_text,
      context,
      path=resolved_path,
      line=script_command.start_line,
    )
    if isinstance(directive, SeedDirective):
      context.seed = directive.value
      print(f"Seed: {directive.value}")
      continue
    if isinstance(directive, LetDirective):
      context.macros[directive.name] = directive.value
      print(f"Macro set: {directive.name}")
      continue

    def run_nested(nested_path: Path) -> _RunStatus:
      return _run_script_status(
        nested_path,
        executor,
        base_dir=resolved_path.parent,
        active_stack=next_stack,
        context=context,
      )

    try:
      status, result = _execute_one(
        expanded_text,
        executor,
        command_rewriter=None,
        run_script=run_nested,
      )
      if result is not None:
        print(format_result(result))
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

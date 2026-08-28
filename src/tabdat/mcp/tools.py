"""Tool handlers and schema declarations for TabDat MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tabdat.doctor import inspect_environment
from tabdat.errors import TabDatError
from tabdat.executor import Executor
from tabdat.formatter import (
  format_error_json,
  format_result,
  format_result_json,
)
from tabdat.help import available_help_topics, load_help_topic_text
from tabdat.mcp.types import (
  MCPCallToolResult,
  MCPTextContent,
  MCPTool,
  MCPToolInputSchema,
)
from tabdat.parser import parse_command

TABDAT_TOOLS: list[MCPTool] = [
  MCPTool(
    name="tabdat_execute",
    description=(
      "Execute a single TabDat command in the active dataset session "
      "(e.g. 'use data.parquet', 'summarize age', 'regress y x', 'histogram age')."
    ),
    inputSchema=MCPToolInputSchema(
      properties={
        "command": {
          "type": "string",
          "description": "The TabDat command string to execute.",
        },
        "output_format": {
          "type": "string",
          "enum": ["terminal", "json"],
          "description": (
            "Desired output format: 'terminal' (table) or 'json' (structured). "
            "Defaults to 'terminal'."
          ),
        },
      },
      required=["command"],
    ),
  ),
  MCPTool(
    name="tabdat_batch",
    description="Execute a sequential list of TabDat commands within the active session.",
    inputSchema=MCPToolInputSchema(
      properties={
        "commands": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Ordered list of TabDat command strings to execute.",
        },
        "output_format": {
          "type": "string",
          "enum": ["terminal", "json"],
          "description": "Format for output results ('terminal' or 'json').",
        },
      },
      required=["commands"],
    ),
  ),
  MCPTool(
    name="tabdat_script",
    description="Execute a full TabDat script (.td file or inline text) in the session.",
    inputSchema=MCPToolInputSchema(
      properties={
        "script_content": {
          "type": "string",
          "description": "Inline TabDat script content containing directives and commands.",
        },
        "file_path": {
          "type": "string",
          "description": "File path to a .td script on disk to execute.",
        },
        "output_format": {
          "type": "string",
          "enum": ["terminal", "json"],
          "description": "Desired output format ('terminal' or 'json').",
        },
      },
      required=[],
    ),
  ),
  MCPTool(
    name="tabdat_status",
    description=(
      "Inspect active session state (dataset, table name, rows, cols, eager/lazy, model)."
    ),
    inputSchema=MCPToolInputSchema(
      properties={
        "output_format": {
          "type": "string",
          "enum": ["terminal", "json"],
          "description": "Output format ('terminal' or 'json'). Defaults to 'terminal'.",
        },
      },
      required=[],
    ),
  ),
  MCPTool(
    name="tabdat_describe_command",
    description=(
      "Get the formal syntax, arguments, options, and help topic for a specific TabDat command."
    ),
    inputSchema=MCPToolInputSchema(
      properties={
        "command_name": {
          "type": "string",
          "description": "Name of the command (e.g. 'regress', 'collapse', 'tabulate').",
        },
      },
      required=["command_name"],
    ),
  ),
  MCPTool(
    name="tabdat_list_commands",
    description=(
      "List all available TabDat commands with declared side effects (read, write, plot, control)."
    ),
    inputSchema=MCPToolInputSchema(
      properties={},
      required=[],
    ),
  ),
  MCPTool(
    name="tabdat_get_help",
    description="Retrieve packaged markdown documentation for any TabDat command or topic.",
    inputSchema=MCPToolInputSchema(
      properties={
        "topic": {
          "type": "string",
          "description": "Name of the help topic (e.g. 'summarize', 'regress', 'sql', 'panel').",
        },
      },
      required=["topic"],
    ),
  ),
  MCPTool(
    name="tabdat_explain",
    description=(
      "Parse and explain a TabDat command's structure and declared effects without executing it."
    ),
    inputSchema=MCPToolInputSchema(
      properties={
        "command": {
          "type": "string",
          "description": "Command string to parse and validate.",
        },
      },
      required=["command"],
    ),
  ),
  MCPTool(
    name="tabdat_doctor",
    description=(
      "Run TabDat environment diagnostics and check availability of DuckDB and backends."
    ),
    inputSchema=MCPToolInputSchema(
      properties={},
      required=[],
    ),
  ),
  MCPTool(
    name="tabdat_reset_session",
    description=(
      "Reset the active session, clearing all loaded tables, variables, and estimation models."
    ),
    inputSchema=MCPToolInputSchema(
      properties={},
      required=[],
    ),
  ),
]


def handle_tool_call(name: str, arguments: dict[str, Any], executor: Executor) -> MCPCallToolResult:
  """Execute an MCP tool call against the active TabDat executor session.

  Args:
    name: The tool name.
    arguments: Dictionary of arguments passed by the MCP client.
    executor: The active TabDat Executor instance.

  Returns:
    An MCPCallToolResult containing text content and error status.
  """
  try:
    if name == "tabdat_execute":
      return _tool_execute(arguments, executor)
    if name == "tabdat_batch":
      return _tool_batch(arguments, executor)
    if name == "tabdat_script":
      return _tool_script(arguments, executor)
    if name == "tabdat_status":
      return _tool_status(arguments, executor)
    if name == "tabdat_describe_command":
      return _tool_describe_command(arguments)
    if name == "tabdat_list_commands":
      return _tool_list_commands()
    if name == "tabdat_get_help":
      return _tool_get_help(arguments)
    if name == "tabdat_explain":
      return _tool_explain(arguments)
    if name == "tabdat_doctor":
      return _tool_doctor(executor)
    if name == "tabdat_reset_session":
      return _tool_reset_session(executor)
    return MCPCallToolResult(
      content=[MCPTextContent(text=f"Unknown tool: {name}")],
      isError=True,
    )
  except Exception as exc:
    return MCPCallToolResult(
      content=[MCPTextContent(text=f"Tool execution failed: {exc}")],
      isError=True,
    )


def _tool_execute(arguments: dict[str, Any], executor: Executor) -> MCPCallToolResult:
  command_str = arguments.get("command")
  if not command_str or not isinstance(command_str, str):
    return MCPCallToolResult(
      content=[MCPTextContent(text="Missing or invalid required argument 'command'.")],
      isError=True,
    )
  output_format = arguments.get("output_format", "terminal")

  try:
    cmd = parse_command(command_str)
    result = executor.execute(cmd)
    if result is None:
      formatted = ""
    else:
      formatted = format_result_json(result) if output_format == "json" else format_result(result)
    return MCPCallToolResult(content=[MCPTextContent(text=formatted)], isError=False)
  except TabDatError as exc:
    formatted_err = format_error_json(exc) if output_format == "json" else f"Error: {exc}"
    return MCPCallToolResult(content=[MCPTextContent(text=formatted_err)], isError=True)


def _tool_batch(arguments: dict[str, Any], executor: Executor) -> MCPCallToolResult:
  commands = arguments.get("commands")
  if not isinstance(commands, list) or not commands:
    return MCPCallToolResult(
      content=[MCPTextContent(text="Missing or empty required list argument 'commands'.")],
      isError=True,
    )
  output_format = arguments.get("output_format", "terminal")

  outputs: list[str] = []
  for cmd_str in commands:
    if not isinstance(cmd_str, str):
      continue
    try:
      cmd = parse_command(cmd_str)
      res = executor.execute(cmd)
      if res is None:
        out = ""
      else:
        out = format_result_json(res) if output_format == "json" else format_result(res)
      outputs.append(f"> {cmd_str}\n{out}")
    except TabDatError as exc:
      err_out = format_error_json(exc) if output_format == "json" else f"> {cmd_str}\nError: {exc}"
      outputs.append(err_out)
      return MCPCallToolResult(
        content=[MCPTextContent(text="\n\n".join(outputs))],
        isError=True,
      )

  return MCPCallToolResult(
    content=[MCPTextContent(text="\n\n".join(outputs))],
    isError=False,
  )


def _tool_script(arguments: dict[str, Any], executor: Executor) -> MCPCallToolResult:
  script_content = arguments.get("script_content")
  file_path = arguments.get("file_path")
  output_format = arguments.get("output_format", "terminal")

  if not script_content and not file_path:
    return MCPCallToolResult(
      content=[MCPTextContent(text="Either 'script_content' or 'file_path' must be provided.")],
      isError=True,
    )

  try:
    if file_path:
      path = Path(file_path)
      if not path.exists():
        return MCPCallToolResult(
          content=[MCPTextContent(text=f"Script file not found: {file_path}")],
          isError=True,
        )
      raw_lines = path.read_text().splitlines()
    else:
      raw_lines = (script_content or "").splitlines()

    lines = [line.strip() for line in raw_lines]

    outputs: list[str] = []
    for line in lines:
      if not line or line.startswith("#"):
        continue
      try:
        cmd = parse_command(line)
        res = executor.execute(cmd)
        if res is None:
          out = ""
        else:
          out = format_result_json(res) if output_format == "json" else format_result(res)
        outputs.append(f"> {line}\n{out}")
      except TabDatError as exc:
        err_out = format_error_json(exc) if output_format == "json" else f"> {line}\nError: {exc}"
        outputs.append(err_out)
        return MCPCallToolResult(
          content=[MCPTextContent(text="\n\n".join(outputs))],
          isError=True,
        )

    summary = "\n\n".join(outputs) if outputs else "Script finished with no output."
    return MCPCallToolResult(
      content=[MCPTextContent(text=summary)],
      isError=False,
    )
  except Exception as exc:
    return MCPCallToolResult(
      content=[MCPTextContent(text=f"Script execution failed: {exc}")],
      isError=True,
    )


def _tool_status(arguments: dict[str, Any], executor: Executor) -> MCPCallToolResult:
  output_format = arguments.get("output_format", "terminal")
  try:
    cmd = parse_command("status")
    result = executor.execute(cmd)
    if result is None:
      formatted = "{}" if output_format == "json" else ""
    else:
      formatted = format_result_json(result) if output_format == "json" else format_result(result)
    return MCPCallToolResult(content=[MCPTextContent(text=formatted)], isError=False)
  except TabDatError as exc:
    return MCPCallToolResult(content=[MCPTextContent(text=f"Error: {exc}")], isError=True)


def _tool_describe_command(arguments: dict[str, Any]) -> MCPCallToolResult:
  from tabdat.cli import _COMMAND_SCHEMAS  # Lazy import to avoid circular dependencies

  command_name = arguments.get("command_name", "").strip().lower()
  if not command_name:
    return MCPCallToolResult(
      content=[MCPTextContent(text="Missing required argument 'command_name'.")],
      isError=True,
    )

  schema = _COMMAND_SCHEMAS.get(command_name)
  if schema is None:
    return MCPCallToolResult(
      content=[
        MCPTextContent(text=f"Command '{command_name}' is not recognized in TabDat schema catalog.")
      ],
      isError=True,
    )

  json_out = format_result_json(schema)
  return MCPCallToolResult(content=[MCPTextContent(text=json_out)], isError=False)


def _tool_list_commands() -> MCPCallToolResult:
  from tabdat.cli import _command_catalog_result, _command_effect_catalog_result

  catalog = _command_catalog_result()
  effects = _command_effect_catalog_result()
  json_out = f"{format_result_json(catalog)}\n{format_result_json(effects)}"
  return MCPCallToolResult(content=[MCPTextContent(text=json_out)], isError=False)


def _tool_get_help(arguments: dict[str, Any]) -> MCPCallToolResult:
  topic = arguments.get("topic", "").strip()
  if not topic:
    return MCPCallToolResult(
      content=[MCPTextContent(text="Missing required argument 'topic'.")],
      isError=True,
    )

  text = load_help_topic_text(topic)
  if text is None:
    available = ", ".join(sorted(available_help_topics()))
    return MCPCallToolResult(
      content=[
        MCPTextContent(text=f"Help topic '{topic}' not found. Available topics: {available}")
      ],
      isError=True,
    )
  return MCPCallToolResult(content=[MCPTextContent(text=text)], isError=False)


def _tool_explain(arguments: dict[str, Any]) -> MCPCallToolResult:
  from tabdat.cli import _command_explain_result

  command_str = arguments.get("command", "").strip()
  if not command_str:
    return MCPCallToolResult(
      content=[MCPTextContent(text="Missing required argument 'command'.")],
      isError=True,
    )

  try:
    explain_result = _command_explain_result(command_str)
    return MCPCallToolResult(
      content=[MCPTextContent(text=format_result_json(explain_result))],
      isError=False,
    )
  except TabDatError as exc:
    return MCPCallToolResult(
      content=[MCPTextContent(text=format_error_json(exc))],
      isError=True,
    )


def _tool_doctor(executor: Executor) -> MCPCallToolResult:
  try:
    doc_result = inspect_environment()
    return MCPCallToolResult(
      content=[MCPTextContent(text=format_result(doc_result))],
      isError=False,
    )
  except Exception as exc:
    return MCPCallToolResult(
      content=[MCPTextContent(text=f"Doctor check failed: {exc}")],
      isError=True,
    )


def _tool_reset_session(executor: Executor) -> MCPCallToolResult:
  try:
    executor.state.active_dataset = None
    executor.state.active_table_name = None
    executor.state.tables.clear()
    executor._clear_all_regression_states()
    return MCPCallToolResult(
      content=[MCPTextContent(text="TabDat session reset successfully. All active data cleared.")],
      isError=False,
    )
  except Exception as exc:
    return MCPCallToolResult(
      content=[MCPTextContent(text=f"Session reset failed: {exc}")],
      isError=True,
    )

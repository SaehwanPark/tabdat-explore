"""Resource handlers and URI declarations for TabDat MCP server."""

from __future__ import annotations

import json
from typing import Any

from tabdat.executor import Executor
from tabdat.formatter import format_result_json
from tabdat.mcp.types import (
  MCPReadResourceResult,
  MCPResource,
  MCPTextResourceContents,
)
from tabdat.parser import parse_command

TABDAT_RESOURCES: list[MCPResource] = [
  MCPResource(
    uri="tabdat://session/status",
    name="Active Session Status",
    description="Live status of the active TabDat session (table, rows, backend, model).",
    mimeType="application/json",
  ),
  MCPResource(
    uri="tabdat://session/schema",
    name="Active Dataset Schema",
    description="Column names and data types of the currently active table.",
    mimeType="application/json",
  ),
  MCPResource(
    uri="tabdat://catalog/commands",
    name="TabDat Command Catalog",
    description="Complete catalog of TabDat commands, syntax, and declared side effects.",
    mimeType="application/json",
  ),
]


def handle_read_resource(uri: str, executor: Executor) -> MCPReadResourceResult:
  """Read a resource by URI from the active TabDat session.

  Args:
    uri: Resource URI string.
    executor: Active TabDat Executor.

  Returns:
    MCPReadResourceResult containing the resource contents.
  """
  if uri == "tabdat://session/status":
    cmd = parse_command("status")
    result = executor.execute(cmd)
    json_text = format_result_json(result) if result is not None else "{}"
    return MCPReadResourceResult(
      contents=[
        MCPTextResourceContents(
          uri=uri,
          mimeType="application/json",
          text=json_text,
        )
      ]
    )

  if uri == "tabdat://session/schema":
    if executor.state.active_dataset is None:
      schema_dict: dict[str, Any] = {"active_table": None, "columns": []}
    else:
      schema_dict = {
        "active_table": executor.state.active_table_name or str(executor.state.active_dataset.path),
        "columns": [
          {"name": col.name, "type": col.data_type} for col in executor.state.active_dataset.columns
        ],
      }
    return MCPReadResourceResult(
      contents=[
        MCPTextResourceContents(
          uri=uri,
          mimeType="application/json",
          text=json.dumps(schema_dict, indent=2),
        )
      ]
    )

  if uri == "tabdat://catalog/commands":
    from tabdat.cli import _command_catalog_result, _command_effect_catalog_result

    catalog = _command_catalog_result()
    effects = _command_effect_catalog_result()
    combined = {
      "catalog": json.loads(format_result_json(catalog)),
      "effects": json.loads(format_result_json(effects)),
    }
    return MCPReadResourceResult(
      contents=[
        MCPTextResourceContents(
          uri=uri,
          mimeType="application/json",
          text=json.dumps(combined, indent=2),
        )
      ]
    )

  raise ValueError(f"Unknown resource URI: {uri}")

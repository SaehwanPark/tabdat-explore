"""Standard JSON-RPC 2.0 stdio server implementation for TabDat MCP."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from typing import Any, TextIO

from tabdat import __version__
from tabdat.config import TabDatConfig, load_default_config
from tabdat.executor import Executor
from tabdat.mcp.prompts import TABDAT_PROMPTS, handle_get_prompt
from tabdat.mcp.resources import TABDAT_RESOURCES, handle_read_resource
from tabdat.mcp.tools import TABDAT_TOOLS, handle_tool_call
from tabdat.mcp.types import (
  JSONRPCErrorData,
  JSONRPCResponse,
  MCPInitializeResult,
  MCPPromptListResult,
  MCPResourceListResult,
  MCPServerCapabilities,
  MCPServerInfo,
  MCPToolListResult,
)


class TabDatMCPServer:
  """Model Context Protocol (MCP) server for TabDat."""

  def __init__(self, config: TabDatConfig | None = None) -> None:
    self.config: TabDatConfig = config if config is not None else load_default_config()
    self.executor: Executor = Executor(config=self.config)
    self.initialized: bool = False

  def close(self) -> None:
    """Close the underlying executor and release resources."""
    self.executor.close()

  def handle_jsonrpc(self, raw_message: str) -> str | None:
    """Parse and dispatch a single JSON-RPC 2.0 message string.

    Args:
      raw_message: Incoming JSON string.

    Returns:
      JSON string response or None if message was a notification.
    """
    try:
      payload = json.loads(raw_message)
    except Exception as exc:
      err = JSONRPCResponse(
        id=None,
        error=JSONRPCErrorData(code=-32700, message=f"Parse error: {exc}"),
      )
      return err.model_dump_json(exclude_none=True)

    if not isinstance(payload, dict):
      err = JSONRPCResponse(
        id=None,
        error=JSONRPCErrorData(code=-32600, message="Invalid Request: expected JSON object"),
      )
      return err.model_dump_json(exclude_none=True)

    msg_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    if not isinstance(method, str):
      if msg_id is not None:
        err = JSONRPCResponse(
          id=msg_id,
          error=JSONRPCErrorData(code=-32600, message="Invalid Request: missing or invalid method"),
        )
        return err.model_dump_json(exclude_none=True)
      return None

    # Handle notifications (no id)
    if msg_id is None:
      self._handle_notification(method, params)
      return None

    # Handle requests (has id)
    response = self._handle_request(msg_id, method, params)
    return response.model_dump_json(exclude_none=True)

  def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
    if method in ("notifications/initialized", "initialized"):
      self.initialized = True

  def _handle_request(
    self,
    msg_id: str | int | None,
    method: str,
    params: dict[str, Any],
  ) -> JSONRPCResponse:
    try:
      if method == "initialize":
        init_result = MCPInitializeResult(
          protocolVersion="2024-11-05",
          capabilities=MCPServerCapabilities(),
          serverInfo=MCPServerInfo(name="tabdat", version=__version__),
        )
        return JSONRPCResponse(id=msg_id, result=init_result.model_dump())

      if method == "ping":
        return JSONRPCResponse(id=msg_id, result={})

      if method == "tools/list":
        tool_list = MCPToolListResult(tools=TABDAT_TOOLS)
        return JSONRPCResponse(id=msg_id, result=tool_list.model_dump())

      if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(tool_name, str):
          return JSONRPCResponse(
            id=msg_id,
            error=JSONRPCErrorData(code=-32602, message="Invalid params: missing tool 'name'"),
          )
        result = handle_tool_call(tool_name, arguments, self.executor)
        return JSONRPCResponse(id=msg_id, result=result.model_dump())

      if method == "resources/list":
        resource_list = MCPResourceListResult(resources=TABDAT_RESOURCES)
        return JSONRPCResponse(id=msg_id, result=resource_list.model_dump())

      if method == "resources/read":
        uri = params.get("uri")
        if not isinstance(uri, str):
          return JSONRPCResponse(
            id=msg_id,
            error=JSONRPCErrorData(code=-32602, message="Invalid params: missing resource 'uri'"),
          )
        res = handle_read_resource(uri, self.executor)
        return JSONRPCResponse(id=msg_id, result=res.model_dump())

      if method == "prompts/list":
        prompt_list = MCPPromptListResult(prompts=TABDAT_PROMPTS)
        return JSONRPCResponse(id=msg_id, result=prompt_list.model_dump())

      if method == "prompts/get":
        prompt_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(prompt_name, str):
          return JSONRPCResponse(
            id=msg_id,
            error=JSONRPCErrorData(code=-32602, message="Invalid params: missing prompt 'name'"),
          )
        p_res = handle_get_prompt(prompt_name, arguments)
        return JSONRPCResponse(id=msg_id, result=p_res.model_dump())

      return JSONRPCResponse(
        id=msg_id,
        error=JSONRPCErrorData(code=-32601, message=f"Method not found: {method}"),
      )
    except Exception as exc:
      return JSONRPCResponse(
        id=msg_id,
        error=JSONRPCErrorData(code=-32603, message=f"Internal server error: {exc}"),
      )

  def run(self, reader: TextIO | None = None, writer: TextIO | None = None) -> None:
    """Run the stdio message processing loop until EOF.

    Args:
      reader: Standard input text stream. Defaults to sys.stdin.
      writer: Standard output text stream. Defaults to sys.stdout.
    """
    in_stream = reader if reader is not None else sys.stdin
    out_stream = writer if writer is not None else sys.stdout
    for line in in_stream:
      stripped = line.strip()
      if not stripped:
        continue
      response_str = self.handle_jsonrpc(stripped)
      if response_str is not None:
        out_stream.write(response_str + "\n")
        out_stream.flush()


def run_mcp_server(
  config: TabDatConfig | None = None,
  reader: TextIO | None = None,
  writer: TextIO | None = None,
) -> int:
  """Run the TabDat MCP server on standard I/O streams.

  Args:
    config: Optional TabDat configuration.
    reader: Optional input stream.
    writer: Optional output stream.

  Returns:
    Exit code 0.
  """
  server = TabDatMCPServer(config=config)
  try:
    server.run(reader=reader, writer=writer)
    return 0
  finally:
    server.close()


def main(argv: Sequence[str] | None = None) -> int:
  """CLI entry point for tabdat-mcp."""
  return run_mcp_server()


if __name__ == "__main__":
  sys.exit(main())

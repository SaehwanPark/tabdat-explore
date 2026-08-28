"""Types and Pydantic models for the Model Context Protocol (MCP) in TabDat."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MCPModel(BaseModel):
  """Base model for all MCP structures with flexible population."""

  model_config = ConfigDict(extra="ignore", populate_by_name=True)


class JSONRPCRequest(MCPModel):
  """A standard JSON-RPC 2.0 request message."""

  jsonrpc: Literal["2.0"] = "2.0"
  id: str | int | None = None
  method: str
  params: dict[str, Any] | None = None


class JSONRPCNotification(MCPModel):
  """A standard JSON-RPC 2.0 notification message (no id)."""

  jsonrpc: Literal["2.0"] = "2.0"
  method: str
  params: dict[str, Any] | None = None


class JSONRPCErrorData(MCPModel):
  """A standard JSON-RPC 2.0 error data object."""

  code: int
  message: str
  data: Any | None = None


class JSONRPCResponse(MCPModel):
  """A standard JSON-RPC 2.0 success or error response."""

  jsonrpc: Literal["2.0"] = "2.0"
  id: str | int | None = None
  result: Any | None = None
  error: JSONRPCErrorData | None = None


class MCPClientInfo(MCPModel):
  """Information about the connected MCP client."""

  name: str
  version: str | None = None


class MCPServerInfo(MCPModel):
  """Information about the TabDat MCP server."""

  name: str = "tabdat"
  version: str


class MCPToolCapability(MCPModel):
  """Tool capability flags."""

  listChanged: bool = False


class MCPResourceCapability(MCPModel):
  """Resource capability flags."""

  subscribe: bool = False
  listChanged: bool = False


class MCPPromptCapability(MCPModel):
  """Prompt capability flags."""

  listChanged: bool = False


class MCPServerCapabilities(MCPModel):
  """Capabilities declared by the TabDat MCP server."""

  tools: MCPToolCapability = Field(default_factory=MCPToolCapability)
  resources: MCPResourceCapability = Field(default_factory=MCPResourceCapability)
  prompts: MCPPromptCapability = Field(default_factory=MCPPromptCapability)


class MCPInitializeParams(MCPModel):
  """Parameters passed to the initialize request."""

  protocolVersion: str = "2024-11-05"
  capabilities: dict[str, Any] = Field(default_factory=dict)
  clientInfo: MCPClientInfo | None = None


class MCPInitializeResult(MCPModel):
  """Result returned by the initialize request."""

  protocolVersion: str = "2024-11-05"
  capabilities: MCPServerCapabilities = Field(default_factory=MCPServerCapabilities)
  serverInfo: MCPServerInfo


class MCPToolInputSchema(MCPModel):
  """JSON Schema defining arguments for an MCP tool."""

  type: Literal["object"] = "object"
  properties: dict[str, dict[str, Any]] = Field(default_factory=dict)
  required: list[str] = Field(default_factory=list)


class MCPTool(MCPModel):
  """Definition of a tool exposed by the TabDat MCP server."""

  name: str
  description: str
  inputSchema: MCPToolInputSchema


class MCPTextContent(MCPModel):
  """Text content returned in tool execution or prompt messages."""

  type: Literal["text"] = "text"
  text: str


class MCPCallToolResult(MCPModel):
  """Result returned by a tool call."""

  content: list[MCPTextContent] = Field(default_factory=list)
  isError: bool = False


class MCPResource(MCPModel):
  """Definition of a resource exposed by TabDat MCP server."""

  uri: str
  name: str
  description: str | None = None
  mimeType: str = "application/json"


class MCPTextResourceContents(MCPModel):
  """Text contents of a resource read operation."""

  uri: str
  mimeType: str = "application/json"
  text: str


class MCPReadResourceResult(MCPModel):
  """Result returned by resources/read."""

  contents: list[MCPTextResourceContents] = Field(default_factory=list)


class MCPPromptArgument(MCPModel):
  """Argument descriptor for an MCP prompt template."""

  name: str
  description: str | None = None
  required: bool = False


class MCPPrompt(MCPModel):
  """Definition of an MCP prompt template."""

  name: str
  description: str | None = None
  arguments: list[MCPPromptArgument] = Field(default_factory=list)


class MCPPromptMessage(MCPModel):
  """A message inside an MCP prompt template response."""

  role: Literal["user", "assistant"] = "user"
  content: MCPTextContent


class MCPGetPromptResult(MCPModel):
  """Result returned by prompts/get."""

  description: str | None = None
  messages: list[MCPPromptMessage] = Field(default_factory=list)


class MCPToolListResult(MCPModel):
  """Result for tools/list."""

  tools: list[MCPTool] = Field(default_factory=list)


class MCPResourceListResult(MCPModel):
  """Result for resources/list."""

  resources: list[MCPResource] = Field(default_factory=list)


class MCPPromptListResult(MCPModel):
  """Result for prompts/list."""

  prompts: list[MCPPrompt] = Field(default_factory=list)

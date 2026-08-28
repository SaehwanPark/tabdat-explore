# Request Summary: TabDat Model Context Protocol (MCP) Server Integration

## 1. Goal
Implement a first-class, lightweight, robust Model Context Protocol (MCP) server for TabDat-Explore that enables AI assistants (Claude Desktop, Cursor, Antigravity, Goose, Cline, etc.) to seamlessly interact with TabDat for tabular exploration, econometric analysis, data transformation, command introspection, and session management over stdio JSON-RPC 2.0.
Follow with full verification, documentation, pull request handoff, and autonomous merge into `main`.

## 2. Touched Surfaces
- `src/tabdat/mcp/`: New submodule containing MCP protocol definitions, JSON-RPC 2.0 transport, tool handlers, resource handlers, prompt templates, and server event loop.
  - `src/tabdat/mcp/__init__.py`: Public exports (`TabDatMCPServer`, `run_mcp_server`).
  - `src/tabdat/mcp/types.py`: Strongly typed Pydantic models for JSON-RPC 2.0 messages, MCP Tool/Resource/Prompt models, and schemas.
  - `src/tabdat/mcp/tools.py`: Tool definitions and executor dispatch handlers (`tabdat_execute`, `tabdat_batch`, `tabdat_script`, `tabdat_status`, `tabdat_describe_command`, `tabdat_list_commands`, `tabdat_get_help`, `tabdat_explain`, `tabdat_doctor`, `tabdat_reset_session`).
  - `src/tabdat/mcp/resources.py`: MCP dynamic URI resources (`tabdat://session/status`, `tabdat://session/schema`, `tabdat://catalog/commands`).
  - `src/tabdat/mcp/prompts.py`: MCP prompt templates (`eda_workflow`, `econometric_analysis`, `data_cleaning`).
  - `src/tabdat/mcp/server.py`: Standard I/O (stdio) JSON-RPC 2.0 server runtime.
- `src/tabdat/cli.py`: Add `--mcp` flag to launch the TabDat MCP server on stdio.
- `pyproject.toml`: Add `tabdat-mcp` console script entrypoint pointing to `tabdat.mcp.server:main`.
- `docs/mcp-server.md`: Comprehensive guide for MCP integration (Claude Desktop config, Cursor config, Antigravity config, tool glossary, resource glossary, prompt glossary).
- `docs/command-reference.md`: Document `--mcp` flag and `tabdat-mcp` entry point.
- `docs/tabdat_forward_roadmap.md`: Update MCP / AI Agent automation milestone.
- `tests/test_mcp.py`: Complete test suite covering JSON-RPC 2.0 handshake, tool execution, session persistence, error recovery, resources, prompts, and CLI invocation.

## 3. Invariants
- Zero heavy mandatory dependencies: MCP server runtime uses stdio + standard library JSON parsing and TabDat's existing Pydantic models with fast startup.
- Complete protocol compliance: Conforms to MCP 2024-11-05 specification (JSON-RPC 2.0, initialize, initialized, ping, tools/list, tools/call, resources/list, resources/read, prompts/list, prompts/get).
- Session statefulness: The MCP server maintains an active `Executor` session across tool calls (e.g. `use` -> `summarize` -> `regress` -> `predict`), with atomic failure guarantees.
- FP style and Type safety: 100% compliant with `basedpyright`, `pydantic`, `tabdat.monads`, and 2-space formatting.

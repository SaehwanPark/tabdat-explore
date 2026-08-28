# TabDat Model Context Protocol (MCP) Server

TabDat includes a built-in Model Context Protocol (MCP) server conforming to the JSON-RPC 2.0 stdio protocol (`protocolVersion: "2024-11-05"`). This enables AI coding agents and LLM applications (such as Claude Desktop, Cursor, Google Antigravity, Goose, Cline, and Windsurf) to directly query, explore, transform, and model tabular datasets with native Stata-inspired command semantics.

---

## 1. Quickstart

### Launch via CLI
Run the MCP server over standard I/O streams:

```bash
tabdat --mcp
```

Or using the dedicated entry point:

```bash
tabdat-mcp
```

---

## 2. Configuration for AI Clients

### Claude Desktop
Add TabDat to your `claude_desktop_config.json` (located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "tabdat": {
      "command": "uvx",
      "args": ["tabdat-explore", "--mcp"]
    }
  }
}
```

If developing locally:

```json
{
  "mcpServers": {
    "tabdat": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/tabdat-explore", "tabdat", "--mcp"]
    }
  }
}
```

### Cursor
Add TabDat to your Cursor MCP settings (`.cursor/mcp.json` or Global Cursor Settings -> MCP):

```json
{
  "mcpServers": {
    "tabdat": {
      "command": "tabdat",
      "args": ["--mcp"]
    }
  }
}
```

### Google Antigravity / Gemini CLI
Add TabDat as an MCP tool provider:

```bash
agy mcp add tabdat tabdat --mcp
```

---

## 3. Available Tools

| Tool Name | Description | Key Arguments |
|---|---|---|
| `tabdat_execute` | Execute a single TabDat command in the active dataset session. | `command` (str, required), `output_format` ("terminal" \| "json") |
| `tabdat_batch` | Execute an ordered list of TabDat commands sequentially. | `commands` (list[str], required), `output_format` ("terminal" \| "json") |
| `tabdat_script` | Run an entire TabDat script file or inline `.td` script content. | `script_content` (str), `file_path` (str), `output_format` |
| `tabdat_status` | Inspect live session state (table name, row count, backend engine, model). | `output_format` ("terminal" \| "json") |
| `tabdat_describe_command` | Look up schema, arguments, options, and syntax for any command. | `command_name` (str, required) |
| `tabdat_list_commands` | List all supported commands and their declared side-effects. | None |
| `tabdat_get_help` | Fetch packaged markdown documentation for any command or topic. | `topic` (str, required) |
| `tabdat_explain` | Parse and validate syntax of a command without running it. | `command` (str, required) |
| `tabdat_doctor` | Check backend availability (DuckDB, Arrow, Polars, Statsmodels, etc.). | None |
| `tabdat_reset_session` | Clear the active session and reset all loaded tables and models. | None |

### Tool Execution Example

An agent calling `tabdat_execute`:

```json
{
  "name": "tabdat_execute",
  "arguments": {
    "command": "use data/synthetic.parquet",
    "output_format": "terminal"
  }
}
```

Followed by modeling:

```json
{
  "name": "tabdat_execute",
  "arguments": {
    "command": "regress income age bmi, robust",
    "output_format": "terminal"
  }
}
```

Session state (loaded datasets, computed variables, active tables, last estimation models) is persisted across consecutive tool calls.

---

## 4. Live Resources

TabDat exposes live dynamic URI resources for real-time state inspection:

| Resource URI | Description | MIME Type |
|---|---|---|
| `tabdat://session/status` | Current session state, active dataset path, row count, and backend mode. | `application/json` |
| `tabdat://session/schema` | Column names and structural datatypes of the active dataset. | `application/json` |
| `tabdat://catalog/commands` | Comprehensive catalog of supported commands and effect categories. | `application/json` |

---

## 5. Guided Prompt Templates

| Prompt Name | Description | Arguments |
|---|---|---|
| `eda_workflow` | Step-by-step exploratory data analysis template. | `file_path` (required), `focus_variables` (optional) |
| `econometric_analysis` | Regression modeling and post-estimation diagnostic workflow. | `file_path` (req), `dependent_var` (req), `independent_vars` (req), `estimator` |
| `data_cleaning` | Variable creation, filtering, recoding, and export template. | `file_path` (req), `task_description` (req) |

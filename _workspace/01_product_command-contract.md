# Product Contract: TabDat Model Context Protocol (MCP) Server

## 1. Overview
The TabDat Model Context Protocol (MCP) server provides a standard, agent-friendly interface to TabDat's tabular data exploration and econometric analysis capabilities. It implements the JSON-RPC 2.0 stdio MCP specification (protocol version `2024-11-05`), exposing tools, resources, and prompt templates for AI agents and LLM tools.

## 2. Protocol & Server Lifecycle

### 2.1 Initialization & Capabilities
- **Request `initialize`**:
  - Responds with server information: `name: "tabdat"`, `version: "<current_version>"`, `protocolVersion: "2024-11-05"`.
  - Declares capabilities:
    - `tools`: `{"listChanged": false}`
    - `resources`: `{"subscribe": false, "listChanged": false}`
    - `prompts`: `{"listChanged": false}`
- **Notification `notifications/initialized`**:
  - Server transitions to active ready state. No response required.
- **Request `ping`**:
  - Responds with `{}`.

### 2.2 Standard Errors
- Returns standard JSON-RPC 2.0 error codes:
  - `-32700`: Parse error (invalid JSON).
  - `-32600`: Invalid Request (malformed structure).
  - `-32601`: Method not found.
  - `-32602`: Invalid params.
  - `-32603`: Internal error.

## 3. Tool Specifications (`tools/list` & `tools/call`)

### 3.1 `tabdat_execute`
- **Description**: "Execute a single TabDat command in the current session (e.g. 'use data.parquet', 'summarize age', 'regress y x1 x2', 'histogram age')."
- **Parameters**:
  - `command` (string, required): The TabDat command string.
  - `output_format` (string, optional, enum: `["terminal", "json"]`, default: `"terminal"`): Format of the execution result.
- **Returns**: `content: [{"type": "text", "text": "..."}]`, `isError: bool`.

### 3.2 `tabdat_batch`
- **Description**: "Execute a list of TabDat commands sequentially within the active session."
- **Parameters**:
  - `commands` (array of strings, required): List of command strings to execute in order.
  - `output_format` (string, optional, enum: `["terminal", "json"]`, default: `"terminal"`): Output format for command results.
- **Returns**: `content: [{"type": "text", "text": "..."}]`, `isError: bool`.

### 3.3 `tabdat_script`
- **Description**: "Execute a TabDat script (.td format) provided as inline text or as a path to an existing script file."
- **Parameters**:
  - `script_content` (string, optional): TabDat script content.
  - `file_path` (string, optional): Path to .td script file.
  - `output_format` (string, optional, enum: `["terminal", "json"]`, default: `"terminal"`).
- **Returns**: Formatted script output and execution summary.

### 3.4 `tabdat_status`
- **Description**: "Inspect the active session state (loaded dataset, active table name, row count, columns, eager/lazy mode, panel settings, latest estimation model)."
- **Parameters**:
  - `output_format` (string, optional, enum: `["terminal", "json"]`, default: `"terminal"`).
- **Returns**: Full status inspection report without forcing materialization.

### 3.5 `tabdat_describe_command`
- **Description**: "Get the formal schema, required arguments, options, and syntax for a TabDat command."
- **Parameters**:
  - `command_name` (string, required): The command to inspect (e.g. 'regress', 'collapse', 'tabulate').
- **Returns**: Structured command schema and syntax definition.

### 3.6 `tabdat_list_commands`
- **Description**: "List all available TabDat commands with their declared side effects (read, write, plot, control) and help availability."
- **Parameters**: None.
- **Returns**: Catalog of commands and effects.

### 3.7 `tabdat_get_help`
- **Description**: "Retrieve the detailed packaged help documentation for any TabDat command or topic."
- **Parameters**:
  - `topic` (string, required): The help topic name (e.g. 'regress', 'summarize', 'panel', 'sql').
- **Returns**: Markdown formatted help documentation.

### 3.8 `tabdat_explain`
- **Description**: "Parse and validate a TabDat command without executing it against data."
- **Parameters**:
  - `command` (string, required): Command string to validate.
- **Returns**: Parsed AST details, argument mapping, and declared effects.

### 3.9 `tabdat_doctor`
- **Description**: "Run TabDat diagnostic checks to inspect installed backends, Python environment, DuckDB, Arrow, and optional statistical stacks."
- **Parameters**: None.
- **Returns**: Diagnostic health check results.

### 3.10 `tabdat_reset_session`
- **Description**: "Reset the active session, clearing all loaded tables, estimation models, and variables."
- **Parameters**: None.
- **Returns**: Confirmation message of session reset.

## 4. Resource Specifications (`resources/list` & `resources/read`)

### 4.1 URIs
- `tabdat://session/status`: Active session state, table name, row count, backend engine.
  - `mimeType`: `"application/json"`
- `tabdat://session/schema`: Column names and data types of the active dataset.
  - `mimeType`: `"application/json"`
- `tabdat://catalog/commands`: Complete catalog of supported TabDat commands and effect categories.
  - `mimeType`: `"application/json"`

## 5. Prompt Specifications (`prompts/list` & `prompts/get`)

### 5.1 Prompts
- `eda_workflow`:
  - Arguments: `file_path` (required), `focus_variables` (optional).
  - Returns message template for initial dataset inspection, summary statistics, missingness checks, and visual exploration.
- `econometric_analysis`:
  - Arguments: `file_path` (required), `dependent_var` (required), `independent_vars` (required), `estimator` (optional, default: `"ols"`).
  - Returns message template for econometric estimation, robust standard errors, collinearity inspection (`estat vif`), and model diagnostics.
- `data_cleaning`:
  - Arguments: `file_path` (required), `task_description` (required).
  - Returns message template for variable creation, filtering, recoding, and data export.

## 6. CLI Surface & Entrypoints
- `tabdat --mcp`: CLI flag to launch stdio MCP server.
- `tabdat-mcp`: Console script entry point in `pyproject.toml`.

## 7. Acceptance Criteria
- [ ] Conforms to MCP JSON-RPC 2.0 stdio specification.
- [ ] Handles `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get`.
- [ ] All 10 tools functional with proper parameter validation and error handling.
- [ ] Session state is preserved across consecutive tool calls (e.g. `use` then `summarize`).
- [ ] Atomic failure: failed commands do not corrupt session state.
- [ ] `tabdat --mcp` and `tabdat-mcp` start and interact correctly over stdio.
- [ ] 100% type-checked (`basedpyright`), formatted & linted (`ruff`), and comprehensive unit tests added in `tests/test_mcp.py`.
- [ ] Documentation updated in `docs/mcp-server.md`, `docs/command-reference.md`, and `README.md`.

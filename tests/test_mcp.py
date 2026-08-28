"""Unit and integration tests for the TabDat Model Context Protocol (MCP) server."""

import io
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tabdat import __version__
from tabdat.cli import main as cli_main
from tabdat.mcp.server import TabDatMCPServer


@pytest.fixture
def sample_parquet(tmp_path: Path) -> Path:
  file_path = tmp_path / "test_data.parquet"
  table = pa.Table.from_arrays(
    [
      pa.array([1, 2, 3, 4, 5]),
      pa.array([20, 25, 30, 35, 40]),
      pa.array([100.0, 150.0, 200.0, 250.0, 300.0]),
    ],
    names=["id", "age", "income"],
  )
  pq.write_table(table, file_path)
  return file_path


def test_mcp_initialize() -> None:
  server = TabDatMCPServer()
  try:
    req = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
          "protocolVersion": "2024-11-05",
          "capabilities": {},
          "clientInfo": {"name": "test-client", "version": "1.0"},
        },
      }
    )
    resp_str = server.handle_jsonrpc(req)
    assert resp_str is not None
    resp = json.loads(resp_str)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["protocolVersion"] == "2024-11-05"
    assert resp["result"]["serverInfo"]["name"] == "tabdat"
    assert resp["result"]["serverInfo"]["version"] == __version__
    assert "tools" in resp["result"]["capabilities"]
    assert "resources" in resp["result"]["capabilities"]
    assert "prompts" in resp["result"]["capabilities"]
  finally:
    server.close()


def test_mcp_ping_and_notifications() -> None:
  server = TabDatMCPServer()
  try:
    # Notification has no response
    notif = json.dumps(
      {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
      }
    )
    resp_str = server.handle_jsonrpc(notif)
    assert resp_str is None
    assert server.initialized is True

    # Ping
    ping = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": "ping-1",
        "method": "ping",
      }
    )
    ping_resp = server.handle_jsonrpc(ping)
    assert ping_resp is not None
    assert json.loads(ping_resp)["result"] == {}
  finally:
    server.close()


def test_mcp_tools_list() -> None:
  server = TabDatMCPServer()
  try:
    req = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
      }
    )
    resp_str = server.handle_jsonrpc(req)
    assert resp_str is not None
    tools = json.loads(resp_str)["result"]["tools"]
    tool_names = {t["name"] for t in tools}
    expected = {
      "tabdat_execute",
      "tabdat_batch",
      "tabdat_script",
      "tabdat_status",
      "tabdat_describe_command",
      "tabdat_list_commands",
      "tabdat_get_help",
      "tabdat_explain",
      "tabdat_doctor",
      "tabdat_reset_session",
    }
    assert expected.issubset(tool_names)
  finally:
    server.close()


def test_mcp_resources_list_and_read(sample_parquet: Path) -> None:
  server = TabDatMCPServer()
  try:
    # List resources
    req = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
    resp_str = server.handle_jsonrpc(req)
    assert resp_str is not None
    resources = json.loads(resp_str)["result"]["resources"]
    uris = {r["uri"] for r in resources}
    assert "tabdat://session/status" in uris
    assert "tabdat://session/schema" in uris
    assert "tabdat://catalog/commands" in uris

    # Read status before data load
    read_status = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "resources/read",
        "params": {"uri": "tabdat://session/status"},
      }
    )
    res_str = server.handle_jsonrpc(read_status)
    assert res_str is not None
    content = json.loads(res_str)["result"]["contents"][0]["text"]
    assert "StatusResult" in content

    # Load dataset
    server.handle_jsonrpc(
      json.dumps(
        {
          "jsonrpc": "2.0",
          "id": 5,
          "method": "tools/call",
          "params": {"name": "tabdat_execute", "arguments": {"command": f"use {sample_parquet}"}},
        }
      )
    )

    # Read schema after data load
    read_schema = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "resources/read",
        "params": {"uri": "tabdat://session/schema"},
      }
    )
    res_schema_str = server.handle_jsonrpc(read_schema)
    assert res_schema_str is not None
    schema_data = json.loads(json.loads(res_schema_str)["result"]["contents"][0]["text"])
    assert schema_data["active_table"] is not None
    col_names = [c["name"] for c in schema_data["columns"]]
    assert col_names == ["id", "age", "income"]

    # Read command catalog
    read_cat = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/read",
        "params": {"uri": "tabdat://catalog/commands"},
      }
    )
    res_cat_str = server.handle_jsonrpc(read_cat)
    assert res_cat_str is not None
    cat_data = json.loads(json.loads(res_cat_str)["result"]["contents"][0]["text"])
    assert "catalog" in cat_data
    assert "effects" in cat_data
  finally:
    server.close()


def test_mcp_prompts_list_and_get() -> None:
  server = TabDatMCPServer()
  try:
    req = json.dumps({"jsonrpc": "2.0", "id": 8, "method": "prompts/list"})
    resp_str = server.handle_jsonrpc(req)
    assert resp_str is not None
    prompts = json.loads(resp_str)["result"]["prompts"]
    p_names = {p["name"] for p in prompts}
    assert {"eda_workflow", "econometric_analysis", "data_cleaning"}.issubset(p_names)

    # Get eda_workflow prompt
    get_p = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "prompts/get",
        "params": {
          "name": "eda_workflow",
          "arguments": {"file_path": "data.parquet", "focus_variables": "age income"},
        },
      }
    )
    p_res_str = server.handle_jsonrpc(get_p)
    assert p_res_str is not None
    p_data = json.loads(p_res_str)["result"]
    assert "EDA Workflow" in p_data["description"]
    assert "age income" in p_data["messages"][0]["content"]["text"]

    # Get econometric_analysis prompt
    get_econ = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "prompts/get",
        "params": {
          "name": "econometric_analysis",
          "arguments": {
            "file_path": "data.parquet",
            "dependent_var": "income",
            "independent_vars": "age",
            "estimator": "robust",
          },
        },
      }
    )
    econ_res_str = server.handle_jsonrpc(get_econ)
    assert econ_res_str is not None
    econ_data = json.loads(econ_res_str)["result"]
    assert "regress income age, robust" in econ_data["messages"][0]["content"]["text"]
  finally:
    server.close()


def test_mcp_tool_workflow_session_persistence(sample_parquet: Path) -> None:
  server = TabDatMCPServer()
  try:
    # 1. Execute `use`
    use_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
          "name": "tabdat_execute",
          "arguments": {"command": f"use {sample_parquet}"},
        },
      }
    )
    res = json.loads(server.handle_jsonrpc(use_call) or "")
    assert res["result"]["isError"] is False
    assert "Loaded" in res["result"]["content"][0]["text"]

    # 2. Execute `summarize` in terminal format
    sum_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
          "name": "tabdat_execute",
          "arguments": {"command": "summarize age income"},
        },
      }
    )
    res_sum = json.loads(server.handle_jsonrpc(sum_call) or "")
    assert res_sum["result"]["isError"] is False
    assert "income" in res_sum["result"]["content"][0]["text"]

    # 3. Execute `generate` in JSON format
    gen_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {
          "name": "tabdat_execute",
          "arguments": {
            "command": "generate age_sq = age * age",
            "output_format": "json",
          },
        },
      }
    )
    res_gen = json.loads(server.handle_jsonrpc(gen_call) or "")
    assert res_gen["result"]["isError"] is False
    assert "TransformResult" in res_gen["result"]["content"][0]["text"]

    # 4. Execute `regress`
    reg_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {
          "name": "tabdat_execute",
          "arguments": {"command": "regress income age"},
        },
      }
    )
    res_reg = json.loads(server.handle_jsonrpc(reg_call) or "")
    assert res_reg["result"]["isError"] is False
    assert "ols" in res_reg["result"]["content"][0]["text"].lower()

    # 5. Execute `predict`
    pred_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "tools/call",
        "params": {
          "name": "tabdat_execute",
          "arguments": {"command": "predict y_hat, xb"},
        },
      }
    )
    res_pred = json.loads(server.handle_jsonrpc(pred_call) or "")
    assert res_pred["result"]["isError"] is False

    # 6. Check `tabdat_status`
    stat_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "tools/call",
        "params": {"name": "tabdat_status", "arguments": {}},
      }
    )
    res_stat = json.loads(server.handle_jsonrpc(stat_call) or "")
    assert res_stat["result"]["isError"] is False
    assert "Backend: duckdb" in res_stat["result"]["content"][0]["text"]
    assert "Rows: 5" in res_stat["result"]["content"][0]["text"]

    # 7. Reset session
    reset_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 17,
        "method": "tools/call",
        "params": {"name": "tabdat_reset_session", "arguments": {}},
      }
    )
    res_reset = json.loads(server.handle_jsonrpc(reset_call) or "")
    assert res_reset["result"]["isError"] is False
    assert "reset successfully" in res_reset["result"]["content"][0]["text"]
  finally:
    server.close()


def test_mcp_batch_and_script_tools(sample_parquet: Path) -> None:
  server = TabDatMCPServer()
  try:
    batch_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 18,
        "method": "tools/call",
        "params": {
          "name": "tabdat_batch",
          "arguments": {
            "commands": [
              f"use {sample_parquet}",
              "summarize age",
              "count",
            ],
          },
        },
      }
    )
    b_res = json.loads(server.handle_jsonrpc(batch_call) or "")
    assert b_res["result"]["isError"] is False
    assert "> count" in b_res["result"]["content"][0]["text"]

    # Script tool with inline text
    script_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 19,
        "method": "tools/call",
        "params": {
          "name": "tabdat_script",
          "arguments": {
            "script_content": "summarize income\ndescribe\n",
          },
        },
      }
    )
    s_res = json.loads(server.handle_jsonrpc(script_call) or "")
    assert s_res["result"]["isError"] is False
    assert "> describe" in s_res["result"]["content"][0]["text"]
  finally:
    server.close()


def test_mcp_introspection_tools() -> None:
  server = TabDatMCPServer()
  try:
    # describe command
    desc_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
          "name": "tabdat_describe_command",
          "arguments": {"command_name": "regress"},
        },
      }
    )
    desc_res = json.loads(server.handle_jsonrpc(desc_call) or "")
    assert desc_res["result"]["isError"] is False
    assert "regress" in desc_res["result"]["content"][0]["text"]

    # get help
    help_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "tools/call",
        "params": {
          "name": "tabdat_get_help",
          "arguments": {"topic": "summarize"},
        },
      }
    )
    help_res = json.loads(server.handle_jsonrpc(help_call) or "")
    assert help_res["result"]["isError"] is False
    assert "summarize" in help_res["result"]["content"][0]["text"]

    # explain
    explain_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 22,
        "method": "tools/call",
        "params": {
          "name": "tabdat_explain",
          "arguments": {"command": "regress y x1 x2, robust"},
        },
      }
    )
    exp_res = json.loads(server.handle_jsonrpc(explain_call) or "")
    assert exp_res["result"]["isError"] is False
    assert "CommandExplainResult" in exp_res["result"]["content"][0]["text"]

    # doctor
    doc_call = json.dumps(
      {
        "jsonrpc": "2.0",
        "id": 23,
        "method": "tools/call",
        "params": {"name": "tabdat_doctor", "arguments": {}},
      }
    )
    doc_res = json.loads(server.handle_jsonrpc(doc_call) or "")
    assert doc_res["result"]["isError"] is False
    assert "TabDat" in doc_res["result"]["content"][0]["text"]
  finally:
    server.close()


def test_mcp_error_handling() -> None:
  server = TabDatMCPServer()
  try:
    # 1. Invalid JSON
    bad_json = server.handle_jsonrpc("not valid json{")
    assert bad_json is not None
    assert json.loads(bad_json)["error"]["code"] == -32700

    # 2. Invalid Request (not an object)
    not_obj = server.handle_jsonrpc("[1, 2, 3]")
    assert not_obj is not None
    assert json.loads(not_obj)["error"]["code"] == -32600

    # 3. Method not found
    unknown = server.handle_jsonrpc(
      json.dumps(
        {
          "jsonrpc": "2.0",
          "id": 99,
          "method": "unknown_method",
        }
      )
    )
    assert unknown is not None
    assert json.loads(unknown)["error"]["code"] == -32601

    # 4. Tool call failure (syntax error in tabdat command)
    tool_err = server.handle_jsonrpc(
      json.dumps(
        {
          "jsonrpc": "2.0",
          "id": 100,
          "method": "tools/call",
          "params": {
            "name": "tabdat_execute",
            "arguments": {"command": "summarize bad syntax $$$"},
          },
        }
      )
    )
    assert tool_err is not None
    res = json.loads(tool_err)["result"]
    assert res["isError"] is True
    assert "Error:" in res["content"][0]["text"]
  finally:
    server.close()


def test_mcp_server_run_stdio_stream() -> None:
  server = TabDatMCPServer()
  try:
    input_stream = io.StringIO(
      json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
      + "\n"
      + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
      + "\n"
    )
    output_stream = io.StringIO()
    server.run(reader=input_stream, writer=output_stream)
    output_lines = [line.strip() for line in output_stream.getvalue().splitlines() if line.strip()]
    assert len(output_lines) == 2
    res1 = json.loads(output_lines[0])
    res2 = json.loads(output_lines[1])
    assert res1["id"] == 1
    assert res1["result"] == {}
    assert res2["id"] == 2
    assert "tools" in res2["result"]
  finally:
    server.close()


def test_cli_mcp_flag(monkeypatch: pytest.MonkeyPatch) -> None:
  input_data = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n")
  output_data = io.StringIO()

  monkeypatch.setattr("sys.stdin", input_data)
  monkeypatch.setattr("sys.stdout", output_data)

  exit_code = cli_main(["--mcp"])
  assert exit_code == 0
  resp = json.loads(output_data.getvalue().strip())
  assert resp["id"] == 1
  assert resp["result"] == {}

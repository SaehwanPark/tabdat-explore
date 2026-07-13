# run

How to invoke:
`run <script-path>`

What it does:
Execute a TabDat script file in the current session.

What problem it answers:
How do I replay a workflow deterministically?

Examples:
- `run analysis.td`

For batch or script execution, `tabdat --json -f analysis.td` emits one compact versioned JSON
result envelope per successful command. JSON mode suppresses script metadata and command echoes;
failures also emit one error envelope with a stable type/message and script location when available;
interactive shell sessions remain terminal-only.

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
interactive shell sessions remain terminal-only.

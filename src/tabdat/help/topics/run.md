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
interactive shell sessions remain terminal-only. Use `tabdat --json --list-commands` for a single
sorted command catalog without starting a session or reading data; discovery cannot be combined with
command or script execution. Use `tabdat --json --help-topic summarize` to retrieve one existing
help topic as a single JSON envelope; topic names are case-insensitive and unknown topics emit the
existing JSON error envelope. Use `tabdat --json --explain -c "summarize age"` for a syntax-only
preview that reports the normalized command name with `execution: "not_run"`; exactly one `-c` is
required and the command is not executed. Standard `--help` keeps argparse help precedence.
Use `tabdat --json --list-command-effects` for the finite declared command-level effect catalog; it
does not start a session, read data, or plan execution.

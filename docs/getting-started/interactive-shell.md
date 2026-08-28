# Interactive Shell

Start TabDat without arguments to enter the interactive shell:

```bash
tabdat
```

You are greeted by the `tabdat>` prompt.

---

## Shell Features

### Context-Aware Autocomplete
TabDat provides real-time inline completions powered by `prompt-toolkit`:
- **Commands**: Typing `reg` suggests `regress`.
- **Active Columns**: Typing `summarize a` autocompletes column names matching `a` from the currently loaded dataset.
- **Options**: Typing `, r` autocompletes options like `, robust` or `, replace`.

### Syntax Highlighting
Commands, keywords, strings, variable names, and SQL blocks are styled with terminal colors for readability.

### Command History
- Use Up and Down arrow keys to cycle through previous commands.
- Press Ctrl+R for reverse-i-search across session history.
- History is saved in `~/.tabdat_history` across sessions.

### Multi-Line SQL
TabDat supports multi-line SQL queries using triple quotes:

```text
tabdat> sql """
......> select sex, avg(bmi) as mean_bmi, count(*) as count
......> from active
......> group by sex
......> order by mean_bmi desc
......> """
```

### In-App Help
Access documentation for any command directly within the REPL:

```text
tabdat> help summarize
tabdat> help regress
tabdat> help did
```

Run `help` with no arguments to list all available topics.

### Exiting the Shell
To exit the interactive session, type `exit` or `quit`, or press Ctrl+D.

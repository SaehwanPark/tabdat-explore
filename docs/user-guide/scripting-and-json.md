# Scripting & Automation

TabDat supports batch execution, script files (`.td`), and machine-readable JSONL envelopes for integration into automated data pipelines and AI agent workflows.

---

## TabDat Scripts (`.td`)

TabDat script files contain sequential TabDat commands executed in a clean batch environment.

### Running Scripts

From the CLI:
```bash
tabdat -f analysis.td
tabdat analysis.td
```

From the interactive shell:
```text
tabdat> run analysis.td
```

---

## Script Directives & Features

### Comments & Clean Execution
- Lines starting with `#` are comments.
- Empty lines are ignored.
- Scripts print run headers, echo executed commands prefixed with `. `, and stop immediately on errors with file and line diagnostics.

### Random Seed
Set random seeds for reproducible estimation and sampling:
```stata
seed 42
```

### Macros & String Interpolation
Define macros with `let` and interpolate them with `$name`:
```stata
let data_file = datasets/cohort_2026.parquet
let outcome = systolic_bp

use $data_file
summarize $outcome
regress $outcome age bmi, robust
```

### Conditionals
Control script flow with `if`, `else`, and `end`:
```stata
if file_exists("data.parquet")
  use data.parquet
else
  use fallback.parquet
end
```

---

## Machine-Readable JSON Mode (`--json`)

Adding `--json` enables structured JSON Lines (JSONL) output for automation:

```bash
tabdat --json -c "use data.parquet" -c "summarize age"
```

### JSON Envelope Format
Each command emits one line of JSON containing:
```json
{
  "schema_version": "1.0",
  "result_type": "summarize",
  "data": {
    "variables": [
      {
        "name": "age",
        "count": 5000,
        "mean": 42.15,
        "std_dev": 11.82,
        "min": 18.0,
        "max": 85.0
      }
    ]
  }
}
```

- Missing values are emitted as `null`.
- Exact decimal numbers are emitted as lossless numeric strings.
- Non-finite floats (`inf`, `-inf`, `nan`) are normalized to `null`.
- Binary payloads are emitted as `base64:<data>` strings.
- Errors emit an `error` envelope with error code, message, and line position.

---

## Machine Discovery Flags

| Flag | Purpose | Example |
|---|---|---|
| `--list-commands` | List all supported commands and their help topic names. | `tabdat --json --list-commands` |
| `--help-topic <name>` | Retrieve the exact packaged documentation for a topic. | `tabdat --json --help-topic regress` |
| `--explain -c "<cmd>"` | Parse and validate syntax without executing or loading data. | `tabdat --json --explain -c "regress y x"` |
| `--list-command-effects` | List declared side-effect categories (`read`, `write`, `control`, `plot`). | `tabdat --json --list-command-effects` |

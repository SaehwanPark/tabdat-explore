#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and populate MkDocs site documentation files for TabDat-Explore."""

import glob
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
SRC_HELP_DIR = REPO_ROOT / "src" / "tabdat" / "help" / "topics"


def build_commands_pages():
  """Convert help topics into rich individual documentation pages under docs/commands/."""
  cmd_dir = DOCS_DIR / "commands"
  cmd_dir.mkdir(parents=True, exist_ok=True)

  topics = sorted(glob.glob(str(SRC_HELP_DIR / "*.md")))
  for topic_file in topics:
    topic_path = Path(topic_file)
    name = topic_path.stem
    content = topic_path.read_text(encoding="utf-8")

    lines = content.splitlines()
    title = name
    invoke_text = ""
    what_it_does = ""
    what_problem = ""
    examples = []
    extra_sections = []

    i = 0
    while i < len(lines):
      line = lines[i].strip()
      if line.startswith("# "):
        title = line[2:].strip()
      elif line.lower().startswith("how to invoke:") or line.lower().startswith("## how to invoke"):
        i += 1
        invokes = []
        while i < len(lines) and not (
          lines[i].startswith("What ")
          or lines[i].startswith("## ")
          or lines[i].startswith("Examples:")
          or lines[i].startswith("Links:")
          or lines[i].startswith("Options:")
        ):
          if lines[i].strip():
            invokes.append(lines[i].strip())
          i += 1
        invoke_text = "\n".join(invokes)
        continue
      elif line.lower().startswith("what it does:") or line.lower().startswith("## what it does"):
        i += 1
        does = []
        while i < len(lines) and not (
          lines[i].startswith("What ")
          or lines[i].startswith("## ")
          or lines[i].startswith("Examples:")
          or lines[i].startswith("Links:")
          or lines[i].startswith("Options:")
          or lines[i].startswith("How to invoke")
        ):
          if lines[i].strip():
            does.append(lines[i].strip())
          i += 1
        what_it_does = "\n\n".join(does)
        continue
      elif (
        line.lower().startswith("what problem it answers:")
        or line.lower().startswith("## what problem")
        or line.lower().startswith("## why use it")
      ):
        i += 1
        probs = []
        while i < len(lines) and not (
          lines[i].startswith("What ")
          or lines[i].startswith("## ")
          or lines[i].startswith("Examples:")
          or lines[i].startswith("Links:")
          or lines[i].startswith("Options:")
          or lines[i].startswith("How to invoke")
        ):
          if lines[i].strip():
            probs.append(lines[i].strip())
          i += 1
        what_problem = "\n\n".join(probs)
        continue
      elif line.lower().startswith("examples:") or line.lower().startswith("## examples"):
        i += 1
        exs = []
        while i < len(lines) and not (
          lines[i].startswith("What ")
          or lines[i].startswith("## ")
          or lines[i].startswith("Links:")
          or lines[i].startswith("Options:")
          or lines[i].startswith("How to invoke")
        ):
          if lines[i].strip():
            exs.append(lines[i].strip())
          i += 1
        examples = exs
        continue
      elif line.lower().startswith("options:") or line.lower().startswith("## options"):
        i += 1
        opts = []
        while i < len(lines) and not (
          lines[i].startswith("What ")
          or lines[i].startswith("## ")
          or lines[i].startswith("Links:")
          or lines[i].startswith("Examples:")
          or lines[i].startswith("How to invoke")
        ):
          if lines[i].strip():
            opts.append(lines[i].strip())
          i += 1
        extra_sections.append(("Options", opts))
        continue
      i += 1

    md = [f"# `{title}`\n"]
    if what_it_does:
      md.append(f"{what_it_does}\n")

    if what_problem:
      md.append('!!! question "When to use"\n    ' + what_problem.replace("\n", "\n    ") + "\n")

    if invoke_text:
      md.append("## Syntax\n")
      clean_invoke = invoke_text.replace("`", "")
      md.append(f"```text\n{clean_invoke}\n```\n")

    for sec_name, sec_lines in extra_sections:
      md.append(f"## {sec_name}\n")
      for sec_line in sec_lines:
        md.append(f"{sec_line}")
      md.append("")

    if examples:
      md.append("## Examples\n")
      md.append("```text")
      for ex in examples:
        clean_ex = ex.lstrip("- ").strip("`")
        md.append(clean_ex)
      md.append("```\n")

    md.append("## See also\n")
    md.append("- [Command Reference Index](../command-reference/index.md)")
    md.append("- [User Guide](../user-guide/index.md)")
    md.append("- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)")
    md.append("")

    out_path = cmd_dir / f"{name}.md"
    out_path.write_text("\n".join(md), encoding="utf-8")

  print(f"Generated {len(topics)} command pages in docs/commands/")


def build_homepage():
  """Create a rich landing page for docs/index.md."""
  content = """# TabDat-Explore

<div align="center">
  <p><strong>Stata-inspired, terminal-native exploratory data analysis for modern tabular data.</strong></p>
  <p>
    <a href="https://github.com/SaehwanPark/tabdat-explore"><img src="https://img.shields.io/badge/GitHub-Repository-blue?logo=github" alt="GitHub"></a>
    <a href="https://github.com/SaehwanPark/tabdat-explore/actions"><img src="https://img.shields.io/badge/CI-Passing-brightgreen?logo=github-actions" alt="CI"></a>
    <img src="https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white" alt="Python 3.13+">
    <img src="https://img.shields.io/badge/Backend-DuckDB%20%7C%20Arrow%20%7C%20Polars-FFD43B" alt="Backends">
    <img src="https://img.shields.io/badge/License-AGPLv3+-red" alt="License">
  </p>
</div>

---

## What is TabDat?

**TabDat-Explore** is a high-performance, command-driven CLI tool for exploratory data analysis (EDA), data cleaning, statistical modeling, and visualization. It combines the concise, fluent syntax of Stata with modern data engineering engines (**DuckDB**, **Apache Arrow**, and **Polars**).

TabDat is **not** a Stata clone: it is built from the ground up for modern columnar datasets (Parquet, Arrow, Feather, CSV, and Stata `.dta`), deterministic execution, terminal UI ergonomics, and integration with AI coding assistants via the Model Context Protocol (MCP).

---

## Key Highlights

=== "⚡ High Performance Engine"
    - **DuckDB & Arrow Core**: Vectorized scans, queries, aggregations, and joins.
    - **Lazy Evaluation**: Scan multi-gigabyte Parquet files without materializing entire tables into RAM until required.
    - **Session Relations**: Zero-copy transformations across commands.

=== "📊 Stata-Inspired Command Flow"
    - **Expressive Syntax**: Intuitive verbs for inspection (`describe`, `summarize`, `codebook`), transformation (`keep`, `drop`, `generate`, `replace`, `recode`), and grouping (`tabulate`, `collapse`, `by`).
    - **Advanced Econometrics**: OLS, robust/cluster standard errors, Logit/Probit, Poisson/NB, IV/2SLS (`ivregress`), fixed/random effects panel (`xtreg`, `xtabond`), difference-in-differences (`did`, `drdid`), regularized ML (`lasso`, `ridge`, `elasticnet`, `dml`), spatial models (`spregress`), and Bayesian MCMC (`bayes:` prefix).

=== "🖥️ Terminal-Native UX"
    - **Interactive REPL**: Auto-completion for command names, columns, and options, with syntax highlighting and persistent history.
    - **Silent Visualization**: Output beautiful plot artifacts (`histogram`, `scatter`, `bar`) silently with clickable `file://` URIs in the terminal.
    - **Reproducible Scripts**: Automate end-to-end workflows in `.td` script files with macros, seeds, and conditionals.

=== "🤖 AI & MCP Integration"
    - **Built-in MCP Server**: Expose TabDat tools, live sessions, dynamic schemas, and prompt templates to AI agents in Claude Desktop, Cursor, Google Antigravity, and Goose.
    - **JSON & Machine Discovery**: Structured JSON/JSONL output envelopes (`--json`), syntax preview (`--explain`), and command introspection (`--list-commands`).

---

## Quickstart

### 1. Install TabDat

```bash
# Recommended 1-line installer (macOS & Linux)
curl -LsSf https://raw.githubusercontent.com/SaehwanPark/tabdat-explore/main/scripts/install.sh | sh
```

Or via Homebrew:
```bash
brew tap SaehwanPark/tabdat https://github.com/SaehwanPark/tabdat-explore.git
brew install tabdat
```

Or via `uv tool`:
```bash
uv tool install git+https://github.com/SaehwanPark/tabdat-explore.git
```

### 2. Launch the Shell

```bash
tabdat
```

```text
tabdat> use data.parquet
Loaded: data.parquet (50000 rows, 8 columns)

tabdat> summarize age income
Variable  Count  Mean     Std Dev  Min   Max
age       50000  41.25    12.41    18    85
income    50000  62450.0  18200.0  1200  245000

tabdat> regress income age educ, robust
Linear regression (OLS, robust HC1)
Dependent variable: income
Observations: 50,000 | R-squared: 0.412 | F-stat: 17520.4 (p < 0.001)

Variable   Coef        Std. Err.   t-stat    P>|t|     [95% Conf. Interval]
age        1245.20     15.30       81.38     <0.001    1215.21   1275.19
educ       3420.50     42.10       81.24     <0.001    3337.98   3503.02
_cons      15200.10    510.40      29.78     <0.001    14199.70  16200.50

tabdat> scatter income age
Plot saved: artifacts/plots/scatter-income-age.png
file:///Users/username/project/artifacts/plots/scatter-income-age.png
```

---

## Documentation Links

- [**Installation & Quickstart**](getting-started/installation.md): All installation methods and prerequisites.
- [**Interactive Shell**](getting-started/interactive-shell.md): Autocomplete, history, and REPL features.
- [**User Guide**](user-guide/index.md): In-depth guides for sessions, diagnostics, scripting, and estimation.
- [**Command Reference**](command-reference/index.md): Complete index and detailed reference for all 69 commands.
- [**MCP Server Guide**](mcp-server.md): Setting up TabDat with Claude Desktop, Cursor, and AI agents.
- [**Statistical Validation Matrix**](reference-validation-matrix.md): Validated numerical precision against reference packages.
- [**Language Semantics**](language-semantics.md): Grammar, missing values, and expression coercion.
- [**Roadmap**](tabdat_forward_roadmap.md): Active development roadmap and milestones.
"""
  (DOCS_DIR / "index.md").write_text(content, encoding="utf-8")
  print("Generated docs/index.md")


def build_getting_started():
  """Create getting-started guides."""
  gs_dir = DOCS_DIR / "getting-started"
  gs_dir.mkdir(parents=True, exist_ok=True)

  (gs_dir / "index.md").write_text(
    """# Getting Started

Welcome to TabDat-Explore! These guides will help you install TabDat, navigate the interactive shell, and run your first exploratory session.

- [**Installation**](installation.md) — 1-line installer, Homebrew, uv tool, and source instructions.
- [**Interactive Shell**](interactive-shell.md) — Shell features, autocomplete, syntax highlighting, and keybindings.
- [**Quickstart Tutorial**](quickstart.md) — Step-by-step walkthrough from data loading to estimation and plotting.
""",
    encoding="utf-8",
  )

  (gs_dir / "installation.md").write_text(
    """# Installation

TabDat-Explore supports macOS (Apple Silicon & Intel) and Linux x86_64 / aarch64.

---

## Recommended: One-Line Installer

Install TabDat globally in seconds:

```bash
curl -LsSf https://raw.githubusercontent.com/SaehwanPark/tabdat-explore/main/scripts/install.sh | sh
```

The installer verifies Python 3.13, fetches the latest distribution wheel, installs the standalone `tabdat` and `tabdat-mcp` executables into `~/.local/bin`, and verifies the installation with `tabdat doctor`.

---

## Homebrew (macOS & Linux)

```bash
brew tap SaehwanPark/tabdat https://github.com/SaehwanPark/tabdat-explore.git
brew install tabdat
```

---

## Using `uv tool`

If you use [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/SaehwanPark/tabdat-explore.git
```

This makes `tabdat` and `tabdat-mcp` available globally in your PATH.

---

## Building from Source

```bash
# Clone repository
git clone https://github.com/SaehwanPark/tabdat-explore.git
cd tabdat-explore

# Install dependencies and sync environment
uv sync

# Run TabDat
uv run tabdat
```

---

## System Diagnostics

After installation, verify your environment and installed backend engines with `doctor`:

```bash
tabdat doctor
```

For automated checks, `tabdat --json doctor` outputs machine-readable JSON envelopes.
""",
    encoding="utf-8",
  )

  (gs_dir / "interactive-shell.md").write_text(
    """# Interactive Shell

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
tabdat> sql \"\"\"
......> select sex, avg(bmi) as mean_bmi, count(*) as count
......> from active
......> group by sex
......> order by mean_bmi desc
......> \"\"\"
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
""",
    encoding="utf-8",
  )

  (gs_dir / "quickstart.md").write_text(
    """# Quickstart Tutorial

This hands-on tutorial walks through loading a dataset, inspecting variables, cleaning data, fitting models, and generating plots.

---

## 1. Load Data

Open a Parquet dataset eagerly:

```text
tabdat> use https://github.com/SaehwanPark/tabdat-explore/raw/main/demos/data/sample.parquet
Loaded: sample.parquet (1000 rows, 6 columns)
```

Or load a local file lazily (deferred scan):

```text
tabdat> use data.parquet, lazy
Active dataset: data.parquet (lazy scan)
```

---

## 2. Inspect Structure and Summary Statistics

Check dataset metadata and schema:

```text
tabdat> describe
Dataset: sample.parquet
Rows: 1000
Columns: 6

Variable  Type     Nulls
id        INTEGER  0
age       INTEGER  12
income    DOUBLE   5
educ      INTEGER  0
married   BOOLEAN  0
score     DOUBLE   18
```

Inspect summary statistics for specific columns:

```text
tabdat> summarize age income score
Variable  Count  Mean     Std Dev  Min   Max
age       988    42.1     11.8     18    79
income    995    58420.0  15400.0  8500  182000
score     982    74.3     14.2     32.0  99.5
```

Profile missingness and sample values with `codebook`:

```text
tabdat> codebook age married
```

---

## 3. Transform and Subset Data

Filter rows:

```text
tabdat> keep if age >= 21
Kept 970 rows (dropped 30)
```

Create derived variables:

```text
tabdat> generate log_income = log(income)
Generated: log_income (DOUBLE)
```

Recode values into categorical groups:

```text
tabdat> recode age (18/35=1) (36/55=2) (56/max=3), generate(age_group)
Generated: age_group (INTEGER)
```

---

## 4. Grouped Summaries and Aggregations

Tabulate frequency distributions:

```text
tabdat> tabulate age_group
age_group  Freq.  Percent  Cum.
1          320    32.99%   32.99%
2          480    49.48%   82.47%
3          170    17.53%   100.00%
Total      970    100.00%
```

Run summaries within groups with `by`:

```text
tabdat> by age_group: summarize income
```

Collapse data into a summary table:

```text
tabdat> collapse (mean) income score (count) n=id, by(age_group)
Collapsed to 3 rows, 4 columns
```

---

## 5. Statistical Estimation

Fit an OLS regression with robust standard errors:

```text
tabdat> regress income age educ, robust
```

Run post-estimation variance inflation factor (VIF) diagnostics:

```text
tabdat> estat vif
Variable  VIF
age       1.12
educ      1.12
Mean VIF  1.12
```

Generate fitted predictions into the active dataset:

```text
tabdat> predict income_hat, xb
Generated: income_hat
```

Generate an interactive HTML diagnostic report:

```text
tabdat> estat report
Report saved: artifacts/reports/regression_report.html
```

---

## 6. Visualization

Plot a histogram of `income`:

```text
tabdat> histogram income
Plot saved: artifacts/plots/histogram-income.png
file:///Users/username/project/artifacts/plots/histogram-income.png
```

Plot a scatter plot with regression line:

```text
tabdat> scatter income age
Plot saved: artifacts/plots/scatter-income-age.png
```

---

## 7. Exporting Results

Save the transformed dataset:

```text
tabdat> save cleaned_data.parquet
Saved: cleaned_data.parquet (970 rows, 8 columns)
```
""",
    encoding="utf-8",
  )

  print("Generated docs/getting-started/ files")


def build_user_guides():
  """Create modular user-guide chapters."""
  ug_dir = DOCS_DIR / "user-guide"
  ug_dir.mkdir(parents=True, exist_ok=True)

  (ug_dir / "index.md").write_text(
    """# TabDat User Guide

This user guide explains how TabDat behaves in everyday use: sessions, data loading, scripting, configuration, visualization, and estimation workflows.

- [**Sessions and the Data Model**](sessions-and-data.md) — The active relation, named tables, and panel metadata.
- [**Loading Data & Diagnostics**](loading-and-diagnostics.md) — Supported formats, eager vs lazy execution, `status`, and `doctor`.
- [**Scripting & Automation**](scripting-and-json.md) — Reproducible `.td` scripts, seed/macro directives, JSON envelope mode, and machine discovery.
- [**Estimation Workflows**](estimation-workflows.md) — Linear, discrete, count, panel, IV, causal, Bayesian, ML, and post-estimation.
- [**Visualization & Artifacts**](visualization.md) — Plot commands, artifact directories, silent plotting, and format settings.
- [**SQL & Persistence**](sql-and-persistence.md) — The `sql` escape hatch, named table creation, `save`, and `export`.
- [**Configuration**](configuration.md) — Startup precedence, `.tabdat.toml`, and XDG paths.
""",
    encoding="utf-8",
  )

  (ug_dir / "sessions-and-data.md").write_text(
    """# Sessions and the Data Model

TabDat operates around an in-memory session model designed for speed, safety, and predictability.

---

## The Active Dataset

At any given time, a TabDat session maintains **one active dataset**. All standard inspection, transformation, modeling, and plotting commands operate directly on this active dataset.

When you execute a transformation (such as `generate`, `replace`, `keep`, `drop`, or `rename`), TabDat updates the active dataset relation:

```text
tabdat> use patients.parquet
Loaded: patients.parquet (1200 rows, 5 columns)

tabdat> generate bmi = weight / (height / 100)^2
Generated: bmi (DOUBLE)
```

---

## Session-Local Named Tables

In addition to the active dataset, a session can maintain named tables in memory.

### Creating Named Tables via SQL
Use the `into <table>` clause in SQL commands to store query results into a named table:

```text
tabdat> sql select sex, avg(bmi) as mean_bmi from active group by sex into summary_by_sex
Created summary_by_sex: 2 rows, 2 columns
```

When created, the new named table immediately becomes the active dataset.

### Switching Between Tables
You can switch back to any named table using `use <table>`:

```text
tabdat> use summary_by_sex
Activated: summary_by_sex (2 rows, 2 columns)
```

Named tables exist purely in memory for the duration of the CLI session. To persist them, use `save` or `export`.

---

## Panel Metadata

Panel data structures are defined using `panel <id_var> <time_var>`:

```text
tabdat> panel id year
Panel declared: id=id, time=year (balanced panel: 500 units x 10 periods)
```

- **Integrity Requirements**: The `(id, time)` pair must have zero missing values and must uniquely identify every row.
- **Scope**: Panel metadata is session-local and retained in memory.
- **Dependent Commands**: Panel-aware commands such as `xtreg`, `xtdata`, `xtlogit`, `xtabond`, and panel `did` require active panel metadata.
- **Clearing Panel Metadata**: Run `panel clear` to remove panel declarations.
""",
    encoding="utf-8",
  )

  (ug_dir / "loading-and-diagnostics.md").write_text(
    """# Loading Data & Diagnostics

TabDat is format-agnostic and Parquet-first, supporting both eager in-memory loading and lazy scan execution.

---

## Supported Formats

| Format | Syntax Example | Notes |
|---|---|---|
| **Parquet** | `use data.parquet` | Native primary format; supports lazy execution. |
| **Stata `.dta`** | `use auto.dta` | Reads Stata 13-118 `.dta` files (local or remote `https://...`). |
| **CSV** | `use data.csv, delimiter(",") has_header(true)` | Configurable delimiters, headers, and type inference. |
| **Feather** | `use data.feather` | Fast Arrow IPC format. |
| **Arrow** | `use data.arrow` | Apache Arrow streaming format. |

---

## Eager vs. Lazy Loading

### Eager Loading (Default)
`use data.parquet` loads the dataset immediately into memory, scans rows, and displays the exact row and column count.

### Lazy Loading
`use data.parquet, lazy` establishes a deferred query plan over the Parquet file without scanning all rows upfront:

```text
tabdat> use large_dataset.parquet, lazy engine=duckdb
Active dataset: large_dataset.parquet (lazy scan)
```

- In lazy mode, row count computation is deferred until `count` or an explicit materializing operation is run.
- The first transformation or estimation command automatically materializes the required relation.

---

## Inspecting Execution State (`status`)

Run `status` at any time to inspect backend execution mode, materialization status, and active relation details without triggering computation:

```text
tabdat> status
Backend: duckdb
Source: large_dataset.parquet
Active table: none
Last operation: use
Execution mode: lazy
Lazy engine: duckdb
Materialization: deferred
Last materialization reason: none
Rows: unknown
Columns: 14
```

---

## Capability Diagnostics (`doctor`)

Run `doctor` to check installed optional libraries, engine versions, and environment capability:

```text
tabdat> doctor
TabDat 0.24.1 Environment Diagnostics

Core Capabilities:
  DuckDB        ✓ duckdb 1.4.3
  PyArrow       ✓ pyarrow 24.0.0
  Polars        ✓ polars 1.36.1
  Plotting      ✓ altair 6.1.0, matplotlib 3.10.9

Statistics:
  statsmodels   ✓ statsmodels 0.14.6
  linearmodels  ✓ linearmodels 7.0
  scipy         ✓ scipy 1.15.0

Optional Capabilities:
  ML            ✓ sklearn 1.7.0
  Bayesian      ✓ bambi 0.18.0
  Spatial       ✓ spreg 1.4.0, libpysal 4.14.1
  R             ✓ rpy2 3.6.4, R binary at /opt/homebrew/bin/R

System:
  Python        ✓ 3.13.2
  Platform      ✓ Darwin (arm64)
```

In automated CI/CD pipelines, `tabdat --json doctor` produces machine-readable diagnostic envelopes.
""",
    encoding="utf-8",
  )

  (ug_dir / "scripting-and-json.md").write_text(
    """# Scripting & Automation

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
""",
    encoding="utf-8",
  )

  (ug_dir / "estimation-workflows.md").write_text(
    """# Estimation Workflows

TabDat provides a comprehensive suite of econometric, statistical, machine learning, and Bayesian estimation commands.

---

## 1. Linear & Quantile Regression

### Classical, Robust & Clustered OLS
```text
tabdat> regress wage educ exper
tabdat> regress wage educ exper, robust
tabdat> regress wage educ exper, cluster(industry)
```

### Quantile Regression
Estimate median or arbitrary conditional quantiles:
```text
tabdat> qreg wage educ exper, quantile(0.5)
tabdat> qreg wage educ exper, quantile(0.9)
```

---

## 2. Binary & Limited Dependent Variables

### Logit & Probit MLE
```text
tabdat> logit employed educ age married, robust
tabdat> probit employed educ age married
```

### Censored Regression (Tobit)
```text
tabdat> tobit hours_worked wage educ, ll(0)
```

### Sample Selection (Heckman)
Two-step Heckman selection estimator:
```text
tabdat> heckman wage educ, selectdep(inwork) select(educ age kids)
```

---

## 3. Count & Survival Data

- **Poisson MLE**: `poisson visits age insurance`
- **Negative Binomial**: `nbreg visits age insurance`
- **Zero-Inflated Poisson**: `zip visits age insurance, inflate(age)`
- **Zero-Inflated Negative Binomial**: `zinb visits age insurance, inflate(age)`
- **Parametric Survival**: `streg duration age, failure(event) dist(weibull)`

---

## 4. Panel Data & Instrumental Variables

### Panel Regression (`xtreg`)
Requires `panel id_var time_var` first:
```text
tabdat> panel firm year
tabdat> xtreg investment capital profit, fe
tabdat> xtreg investment capital profit, re
```

### Dynamic Panel GMM (`xtabond`)
Arellano-Bond linear dynamic panel estimator:
```text
tabdat> xtabond investment capital profit, lags(1)
```

### Instrumental Variables (`ivregress`)
Two-stage least squares (2SLS) and GMM:
```text
tabdat> ivregress 2sls wage exper, endog(educ) iv(near_college parents_educ)
```

---

## 5. Causal Inference

### Difference-in-Differences (`did`)
```text
tabdat> did outcome, treat(treated) post(post_period)
```

### Doubly Robust Difference-in-Differences (`drdid`)
```text
tabdat> drdid outcome covariates, treat(treated) post(post_period)
```

---

## 6. Regularization & Machine Learning

- **Lasso**: `lasso linear y x1 x2 x3`
- **Post-Lasso OLS**: `postlasso linear y x1 x2 x3`
- **Ridge Regression**: `ridge linear y x1 x2 x3`
- **Elastic Net**: `elasticnet linear y x1 x2 x3, l1_ratio(0.5)`
- **Cross-Validated Models**: `cvlasso linear y x1 x2 x3`, `cvridge ...`, `cvelasticnet ...`
- **Double/Debiased Machine Learning (DML)**: `dml linear y controls, treat(t)`

---

## 7. Bayesian Estimation

### Bayesian Ridge Linear Regression
```text
tabdat> bayes linear wage educ exper
```

### Full MCMC Sampling (`bayes:` Prefix)
MCMC estimation via Bambi/PyMC backends with custom priors:
```text
tabdat> bayes, draws(2000) burnin(1000) chains(4): regress wage educ exper
```

- **MCMC Diagnostics**: `estat bayes`
- **MCMC Trace Plots**: `bayesplot trace`, `bayesplot density`, `bayesplot autocorrelation`
- **Posterior Predictive Predictions**: `predict wage_pp, posterior_predictive std interval`

---

## 8. Spatial Econometrics (`spregress`)

Fit spatial lag (SAR) and spatial error (SEM) models:
```text
tabdat> spregress crime income, coord(lat lon) model(lag)
```

---

## 9. Post-Estimation Diagnostics

- `predict <varname>, xb`: Compute linear predictions.
- `predict <varname>, residuals`: Compute residuals.
- `predict <varname>, pr`: Predicted probabilities (after Logit/Probit).
- `estat vif`: Multicollinearity variance inflation factors.
- `estat report`: Generate self-contained HTML regression summary report.
- `test x1 = x2`: Linear hypothesis Wald tests.
- `lincom x1 + 2*x2`: Estimate linear combinations of parameters.
""",
    encoding="utf-8",
  )

  (ug_dir / "visualization.md").write_text(
    """# Visualization & Artifacts

TabDat follows a **terminal-first, silent-by-default** visualization philosophy. Plots are rendered into clean static image artifacts (PNG, SVG, PDF) and saved to disk without popping intrusive GUI windows.

---

## Plot Commands

### 1. Histogram (`histogram`)
Plot the empirical distribution of a continuous variable:

```text
tabdat> histogram income
Plot saved: artifacts/plots/histogram-income.png
file:///Users/username/project/artifacts/plots/histogram-income.png
```

Specify custom bins or frequency mode:
```text
tabdat> histogram income, bins(30) freq
```

### 2. Scatter Plot (`scatter`)
Generate a bivariate scatter plot with optional fit line:

```text
tabdat> scatter income age
Plot saved: artifacts/plots/scatter-income-age.png
```

### 3. Categorical Bar Chart (`bar`)
Display frequency distributions for categorical variables:

```text
tabdat> bar education_level
Plot saved: artifacts/plots/bar-education_level.png
```

Include missing categories with `, missing`:
```text
tabdat> bar education_level, missing
```

### 4. Bayesian MCMC Diagnostics (`bayesplot`)
Generate MCMC diagnostic plots after fitting a `bayes:` model:

```text
tabdat> bayes: regress wage educ exper
tabdat> bayesplot trace
tabdat> bayesplot density
tabdat> bayesplot autocorrelation
```

---

## Plot Settings & Configuration

| Setting | Values | Default | Description |
|---|---|---|---|
| `graph_format` | `png`, `svg`, `pdf` | `png` | Image file format for saved plots. |
| `artifact_dir` | Path string | `artifacts` | Root directory for plot and report artifacts. |
| `graph_open` | `true`, `false` | `false` | If `true`, automatically launches system image viewer. |

Change settings interactively with `set`:
```text
tabdat> set graph_format svg
tabdat> set artifact_dir figures
tabdat> set graph_open false
```

Or pass explicit output paths using `saving(...)`:
```text
tabdat> histogram age, saving(figures/age_dist.svg)
```
""",
    encoding="utf-8",
  )

  (ug_dir / "sql-and-persistence.md").write_text(
    """# SQL & Persistence

TabDat integrates DuckDB SQL directly into the interactive session and script workflows, providing an escape hatch for ad-hoc queries, joins, and window functions.

---

## The `sql` Command

The active dataset is exposed to SQL queries under the table name `active`:

```text
tabdat> sql select sex, avg(bmi) as avg_bmi from active group by sex
sex  avg_bmi
F    24.8
M    26.2
```

---

## Creating Named Tables with `into <table>`

You can direct the output of any SQL query into a session-local named table:

```text
tabdat> sql select age, avg(income) as mean_income from active group by age order by age into age_summary
Created age_summary: 45 rows, 2 columns
```

This creates `age_summary` in memory and makes it the active dataset. You can return to it later via `use age_summary`.

---

## Persistence: `save` and `export`

To persist the active dataset to disk as a standard Apache Parquet file, use `save` or `export`:

```text
tabdat> save cleaned_cohort.parquet
Saved: cleaned_cohort.parquet (15000 rows, 12 columns)
```

### Overwrite Protection
If the destination file already exists, TabDat prevents accidental overwrites unless you explicitly supply `, replace`:

```text
tabdat> save cleaned_cohort.parquet, replace
Overwritten: cleaned_cohort.parquet (15000 rows, 12 columns)
```
""",
    encoding="utf-8",
  )

  (ug_dir / "configuration.md").write_text(
    """# Configuration

TabDat supports runtime session configuration, project-level `.tabdat.toml` files, and user-level XDG global settings.

---

## Precedence Hierarchy

Configuration values are resolved in the following priority (highest to lowest):

1. **CLI Flags**: Explicit command-line arguments (e.g. `--config custom.toml`).
2. **Project Config**: `.tabdat.toml` located in the current working directory.
3. **User Global Config**: `~/.config/tabdat/config.toml` (or `$XDG_CONFIG_HOME/tabdat/config.toml`).
4. **Internal Defaults**: Built-in defaults (`graph_format="png"`, `artifact_dir="artifacts"`, `graph_open=false`).

---

## Configuration Keys

| Key | Type | Default | Description |
|---|---|---|---|
| `graph_format` | `string` | `"png"` | Plot output format (`"png"`, `"svg"`, `"pdf"`). |
| `artifact_dir` | `string` | `"artifacts"` | Directory for saved plot and report artifacts. |
| `graph_open` | `boolean` | `false` | Whether to automatically open plots in default GUI viewer. |

---

## Example `.tabdat.toml`

```toml
# .tabdat.toml (Project Root)
graph_format = "svg"
artifact_dir = "output/figures"
graph_open = false
```

Load a specific configuration file when executing scripts:

```bash
tabdat --config production.toml -f pipeline.td
```
""",
    encoding="utf-8",
  )

  print("Generated docs/user-guide/ files")


def build_command_reference():
  """Create command-reference category pages and index."""
  cr_dir = DOCS_DIR / "command-reference"
  cr_dir.mkdir(parents=True, exist_ok=True)

  (cr_dir / "index.md").write_text(
    """# Command Reference Index

TabDat-Explore includes 69 commands and topics organized into functional categories. Click any command name to view its syntax, options, and examples.

---

## Load & Inspect
| Command | Purpose |
|---|---|
| [`use`](../commands/use.md) | Load a dataset from Parquet, Stata `.dta`, CSV, Arrow, or activate a named table. |
| [`describe`](../commands/describe.md) | Show dataset shape, variable names, and DuckDB/Arrow data types. |
| [`summarize`](../commands/summarize.md) | Descriptive statistics (count, mean, std dev, min, max) for numeric variables. |
| [`codebook`](../commands/codebook.md) | Detailed variable profiling with missingness and unique sample values. |
| [`count`](../commands/count.md) | Count rows in the active dataset. |
| [`head`](../commands/head.md) | Preview the first rows of the active dataset. |
| [`tail`](../commands/tail.md) | Preview the last rows of the active dataset. |
| [`status`](../commands/status.md) | Show execution backend state, materialization status, and active relation details. |
| [`doctor`](../commands/doctor.md) | Inspect environment, core engines, and capability health. |

---

## Transform & Subset
| Command | Purpose |
|---|---|
| [`keep`](../commands/keep.md) | Keep specific variables or rows matching a boolean condition. |
| [`drop`](../commands/drop.md) | Drop specific variables or rows matching a boolean condition. |
| [`select`](../commands/select.md) | Select a subset of columns into the active dataset. |
| [`generate`](../commands/generate.md) | Create a new variable from an arithmetic or logical expression. |
| [`replace`](../commands/replace.md) | Replace values in an existing variable conditionally or unconditionally. |
| [`rename`](../commands/rename.md) | Rename variables in the active dataset. |
| [`recode`](../commands/recode.md) | Recode values or ranges into new categories. |

---

## Combine & Reshape
| Command | Purpose |
|---|---|
| [`join`](../commands/join.md) | Join the active dataset with a named table or file on key variables. |
| [`append`](../commands/append.md) | Vertically stack rows from a named table to the active dataset. |
| [`reshape`](../commands/reshape.md) | Reshape data between wide and long layouts. |

---

## Summarize & Tabulate
| Command | Purpose |
|---|---|
| [`tabulate`](../commands/tabulate.md) | One-way and two-way frequency tables and crosstabs. |
| [`collapse`](../commands/collapse.md) | Grouped aggregations (mean, sum, min, max, count) into a new dataset. |
| [`by`](../commands/by.md) | Execute a command independently within groups of variables. |

---

## Linear & Quantile Models
| Command | Purpose |
|---|---|
| [`regress`](../commands/regress.md) | Linear regression (OLS, WLS, GLS) with robust and clustered covariance. |
| [`qreg`](../commands/qreg.md) | Quantile regression for median and conditional quantiles. |

---

## Binary & Limited Dependent Variables
| Command | Purpose |
|---|---|
| [`logit`](../commands/logit.md) | Logistic regression via maximum likelihood. |
| [`probit`](../commands/probit.md) | Probit regression via maximum likelihood. |
| [`tobit`](../commands/tobit.md) | Tobit censored regression with lower and upper bounds. |
| [`heckman`](../commands/heckman.md) | Heckman two-step sample selection estimator. |
| [`nl`](../commands/nl.md) | Nonlinear least squares regression. |

---

## Count & Survival Models
| Command | Purpose |
|---|---|
| [`poisson`](../commands/poisson.md) | Poisson log-linear count regression. |
| [`nbreg`](../commands/nbreg.md) | Negative binomial count regression. |
| [`zip`](../commands/zip.md) | Zero-inflated Poisson count regression. |
| [`zinb`](../commands/zinb.md) | Zero-inflated negative binomial regression. |
| [`streg`](../commands/streg.md) | Parametric survival regression (Weibull, Exponential, Cox). |

---

## Panel, IV & Causal Inference
| Command | Purpose |
|---|---|
| [`panel`](../commands/panel.md) | Set, display, or clear panel identifier and time metadata. |
| [`ivregress`](../commands/ivregress.md) | Instrumental variables regression (2SLS and GMM). |
| [`cfregress`](../commands/cfregress.md) | Control function regression for endogeneity. |
| [`xtreg`](../commands/xtreg.md) | Panel data fixed-effects (FE) and random-effects (RE) models. |
| [`xtdata`](../commands/xtdata.md) | Panel within and between transformations. |
| [`xtlogit`](../commands/xtlogit.md) | Fixed-effects conditional logit regression. |
| [`xtabond`](../commands/xtabond.md) | Arellano-Bond dynamic panel GMM estimator. |
| [`did`](../commands/did.md) | Difference-in-differences estimator with panel metadata. |
| [`drdid`](../commands/drdid.md) | Doubly robust difference-in-differences estimator. |

---

## Machine Learning & Regularization
| Command | Purpose |
|---|---|
| [`lasso`](../commands/lasso.md) | L1-regularized Lasso linear regression. |
| [`postlasso`](../commands/postlasso.md) | Post-selection OLS estimation after Lasso. |
| [`ridge`](../commands/ridge.md) | L2-regularized Ridge linear regression. |
| [`elasticnet`](../commands/elasticnet.md) | Elastic net regression with combined L1/L2 penalties. |
| [`cvlasso`](../commands/cvlasso.md) | Cross-validated Lasso with optimal penalty selection. |
| [`cvridge`](../commands/cvridge.md) | Cross-validated Ridge regression. |
| [`cvelasticnet`](../commands/cvelasticnet.md) | Cross-validated Elastic net regression. |
| [`dml`](../commands/dml.md) | Double / debiased machine learning average treatment effect (ATE). |

---

## Bayesian & Spatial
| Command | Purpose |
|---|---|
| [`bayes`](../commands/bayes.md) | Bayesian linear regression via Ridge estimation. |
| [`bayes_prefix`](../commands/bayes_prefix.md) | MCMC sampling prefix for linear and logistic regression models. |
| [`bayesplot`](../commands/bayesplot.md) | MCMC chain diagnostic plots (trace, density, autocorrelation). |
| [`spregress`](../commands/spregress.md) | Spatial lag (SAR) and spatial error (SEM) regression models. |

---

## Post-Estimation & Hypothesis Tests
| Command | Purpose |
|---|---|
| [`predict`](../commands/predict.md) | Compute fitted values (`xb`), residuals, probabilities (`pr`), or draws. |
| [`estat`](../commands/estat.md) | Post-estimation diagnostics (VIF, AIC/BIC, Hausman test, etc.). |
| [`estat_report`](../commands/estat_report.md) | Generate self-contained HTML regression diagnostic report. |
| [`test`](../commands/regress.md) | Linear hypothesis Wald test after regression. |
| [`lincom`](../commands/regress.md) | Estimate linear combinations of model parameters. |
| [`ttest`](../commands/summarize.md) | Student t-tests for one sample, two samples, or paired observations. |

---

## Visualization
| Command | Purpose |
|---|---|
| [`histogram`](../commands/histogram.md) | Save frequency or density histogram plots. |
| [`scatter`](../commands/scatter.md) | Save bivariate scatter plots with optional fit lines. |
| [`bar`](../commands/bar.md) | Save categorical bar charts. |

---

## Scripts, SQL & System
| Command | Purpose |
|---|---|
| [`sql`](../commands/sql.md) | Run DuckDB SQL queries against the active dataset. |
| [`run`](../commands/run.md) | Execute a `.td` script file. |
| [`save`](../commands/save.md) | Save the active dataset to Parquet. |
| [`export`](../commands/export.md) | Export the active dataset to Parquet. |
| [`set`](../commands/set.md) | Configure session runtime settings (`graph_format`, `artifact_dir`, `graph_open`). |
| [`lowess`](../commands/lowess.md) | Locally weighted scatterplot smoothing (LOWESS). |
| [`help`](../commands/describe.md) | Display in-app help for commands and topics. |
| [`exit`](../commands/exit.md) / [`quit`](../commands/quit.md) | Exit the interactive shell. |
""",
    encoding="utf-8",
  )

  print("Generated docs/command-reference/index.md")


def build_auxiliary_docs():
  """Copy or adapt repo-root documents into docs/."""
  contrib = REPO_ROOT / "CONTRIBUTING.md"
  if contrib.exists():
    text = contrib.read_text(encoding="utf-8")
    # Adjust relative links for docs/
    text = text.replace(
      "[AGENTS.md](AGENTS.md)",
      "[AGENTS.md](https://github.com/SaehwanPark/tabdat-explore/blob/main/AGENTS.md)",
    )
    text = text.replace("[ARCHITECTURE.md](ARCHITECTURE.md)", "[ARCHITECTURE.md](architecture.md)")
    text = text.replace(
      "[SPEC.md](SPEC.md)",
      "[SPEC.md](https://github.com/SaehwanPark/tabdat-explore/blob/main/SPEC.md)",
    )
    # Strip docs/ prefix in links
    text = re.sub(r"\]\(docs/([^)]+)\)", r"](\1)", text)
    (DOCS_DIR / "contributing.md").write_text(text, encoding="utf-8")
    print("Generated docs/contributing.md")

  arch = REPO_ROOT / "ARCHITECTURE.md"
  if arch.exists():
    text = arch.read_text(encoding="utf-8")
    text = text.replace("[User guide](docs/user-guide.md)", "[User guide](user-guide/index.md)")
    text = re.sub(r"\]\(docs/([^)]+)\)", r"](\1)", text)
    (DOCS_DIR / "architecture.md").write_text(text, encoding="utf-8")
    print("Generated docs/architecture.md")

  # Remove legacy roadmap.md if present
  old_roadmap = DOCS_DIR / "roadmap.md"
  if old_roadmap.exists():
    old_roadmap.unlink()


def build_mkdocs_config():
  """Write mkdocs.yml with full navigation."""
  topics = sorted(glob.glob(str(SRC_HELP_DIR / "*.md")))
  command_nav = []
  for t in topics:
    stem = Path(t).stem
    command_nav.append(f"          - {stem}: commands/{stem}.md")

  cmd_nav_str = "\n".join(command_nav)

  mkdocs_content = f"""site_name: TabDat-Explore
site_description: Stata-inspired, terminal-native exploratory data analysis for modern tabular data
site_author: Sae-Hwan Park
site_url: https://saehwanpark.github.io/tabdat-explore/
repo_name: SaehwanPark/tabdat-explore
repo_url: https://github.com/SaehwanPark/tabdat-explore
edit_uri: edit/main/docs/

theme:
  name: material
  language: en
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - navigation.footer
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate
    - content.tabs.link

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.snippets
  - tables
  - attr_list
  - def_list
  - toc:
      permalink: true

nav:
  - Home: index.md
  - Getting Started:
      - Overview: getting-started/index.md
      - Installation: getting-started/installation.md
      - Interactive Shell: getting-started/interactive-shell.md
      - Quickstart Tutorial: getting-started/quickstart.md
  - User Guide:
      - Overview: user-guide/index.md
      - Sessions & Data Model: user-guide/sessions-and-data.md
      - Loading & Diagnostics: user-guide/loading-and-diagnostics.md
      - Scripting & Automation: user-guide/scripting-and-json.md
      - Estimation Workflows: user-guide/estimation-workflows.md
      - Visualization & Artifacts: user-guide/visualization.md
      - SQL & Persistence: user-guide/sql-and-persistence.md
      - Configuration: user-guide/configuration.md
      - Unified User Guide: user-guide.md
  - Command Reference:
      - Index & Categories: command-reference/index.md
      - Unified Command Reference: command-reference.md
      - Commands:
{cmd_nav_str}
  - AI & Protocols:
      - MCP Server: mcp-server.md
  - Statistical Rigor:
      - Validation Matrix: reference-validation-matrix.md
      - Microeconometrics Topics: microecometrics_topics.md
  - Architecture & Specifications:
      - Language Semantics: language-semantics.md
      - Distribution Strategy ADR: adr/0001-distribution-and-packaging-strategy.md
      - Active Roadmap: tabdat_forward_roadmap.md
      - Architecture: architecture.md
      - Contributing: contributing.md
      - Team Spec: harness/tabdat/team-spec.md
  - Development & Historical Specs:
      - Project Proposal: project_proposal.md
      - Development Phases: dev_phase.md
      - Phase 0 Guardrails: phase0_product_guardrails.md
      - Phase 0 Command Glossary: command_glossary_v0.md
      - Public Dataset Test Plan: e2e_public_dataset_test_plan.md
      - Project Feedback (2026-05): project_feedback_20260504.md
"""
  (REPO_ROOT / "mkdocs.yml").write_text(mkdocs_content, encoding="utf-8")
  print("Generated mkdocs.yml")


def main():
  print("Building full documentation hierarchy for MkDocs & GitHub Pages...")
  build_commands_pages()
  build_homepage()
  build_getting_started()
  build_user_guides()
  build_command_reference()
  build_auxiliary_docs()
  build_mkdocs_config()
  print("Documentation structure built successfully!")


if __name__ == "__main__":
  main()

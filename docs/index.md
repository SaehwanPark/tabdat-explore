# TabDat-Explore

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

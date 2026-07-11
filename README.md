# TabDat-Explore

TabDat-Explore is a terminal-native exploratory data analysis tool for modern tabular data. It
feels Stata-inspired, but it is **not** Stata-compatible.

## Who it's for

TabDat is built for people who want fast, command-driven data work in a terminal:

- **Statisticians and analysts** who like concise inspection and summary workflows
- **CLI-oriented data scientists** who want reproducible scripts without notebook overhead
- **Engineers and analysts working with Parquet** who need lightweight local exploration

## Why TabDat

- **Fast terminal EDA** — inspect, filter, summarize, and plot without leaving the shell
- **Scriptable workflows** — save repeatable analysis in `.td` script files
- **Modern tabular formats** — Parquet-first, with CSV, Feather, Arrow, and Stata `.dta` support
- **Concise commands** — expressive syntax for routine tasks, with SQL when you need it

See the [project proposal](docs/project_proposal.md) for the full product vision. Release history
is in [CHANGELOG.md](CHANGELOG.md).

## Quickstart

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

### Install from source

PyPI publication is planned. For now, install from the repository:

```bash
git clone https://github.com/SaehwanPark/tabdat-explore.git
cd tabdat-explore
uv sync
```

### First run

Run a few commands against a Parquet file:

```bash
uv run tabdat -c "use data.parquet" -c "describe" -c "summarize age bmi"
```

### Interactive shell

Start the shell and work at the `tabdat>` prompt:

```bash
uv run tabdat
```

The shell provides command history, syntax highlighting, inline history suggestions, and
context-aware autocomplete.

### Discover commands

Use in-app help for syntax and options:

```text
tabdat> help use
tabdat> help summarize
```

Or in batch mode:

```bash
uv run tabdat -c "help regress"
```

For lazy loading, scripts, configuration, and plots, see the [user guide](docs/user-guide.md).

## Example session

```text
tabdat> use data.parquet
Loaded: data.parquet (3 rows, 4 columns)

tabdat> describe
Dataset: data.parquet
Rows: 3
Columns: 4

Variable  Type
age       INTEGER
bmi       DOUBLE
sex       VARCHAR
cost      DOUBLE

tabdat> help summarize
# ... in-app help for summarize ...

tabdat> summarize age bmi
Variable  Count  Mean  Std Dev  Min  Max
age       3      42    12       30   54
bmi       3      25    2.5      22.5  27.5

tabdat> sql select sex, avg(bmi) as mean_bmi from active group by sex order by sex
sex  mean_bmi
F    25
M    25

tabdat> sql select sex, count(*) as n from active group by sex into summary
Created summary: 2 rows, 2 columns

tabdat> use summary
Activated: summary (2 rows, 2 columns)

tabdat> save transformed.parquet
Saved: transformed.parquet (3 rows, 4 columns)

tabdat> run analysis.td
```

Panel metadata, plot defaults, and other session details are covered in the
[user guide](docs/user-guide.md).

## What you can do

| Area | Commands | What they help with |
|------|----------|---------------------|
| Load and inspect | `use`, `describe`, `summarize`, `codebook`, `head`, `count` | Open data and understand structure |
| Transform | `keep`, `drop`, `select`, `generate`, `rename`, `recode` | Filter, reshape, and derive columns |
| Summarize | `tabulate`, `collapse`, `by` | Frequencies, crosstabs, and grouped stats |
| Model | `regress`, `logit`, `ivregress`, `xtreg`, `qreg`, … | Linear, binary, IV, panel, and more |
| ML and causal | `lasso`, `dml`, `bayes`, `spregress`, `drdid`, … | Regularization, Bayesian, spatial, DID |
| Visualize | `histogram`, `scatter`, `bar` | Save plot artifacts from the shell |
| Scripts and I/O | `run`, `save`, `export`, `sql` | Reproducible scripts and Parquet output |

**Full syntax and options:** [command reference](docs/command-reference.md) and `help <command>`.

## Learn more

- [User guide](docs/user-guide.md) — sessions, lazy loading, scripts, config, plots, estimation
- [Command reference](docs/command-reference.md) — categorized command index
- [Project proposal](docs/project_proposal.md) — product vision (optional deep read)

## Contributing

Interested in developing TabDat? See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, validation
commands, and links to architecture and spec docs.

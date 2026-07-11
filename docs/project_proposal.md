---
title: "Project Proposal"
author: "Sae-Hwan Park"
date: 2026-05-02
description: "a structured project document that captures the idea clearly and is suitable for a README, design doc, or proposal."
---

# Project Proposal: CLI-Based EDA Tool with Modern Data Support

## 1. Overview

This project proposes the development of a **command-line exploratory data analysis (EDA) tool** that combines:

* **Stata-inspired command ergonomics**
* **Modern data infrastructure (Parquet, Arrow, Stata `.dta`, lazy execution)**
* **Terminal-native user experience (autocomplete, syntax highlighting)**

The goal is not to replicate legacy statistical software, but to **reimagine the command-driven workflow** for contemporary data environments.

This tool will provide a fast, expressive, and reproducible interface for inspecting, transforming, and summarizing tabular data—especially datasets that are large, columnar, and not fully memory-resident.

---

## 2. Purpose

The primary purpose is to fill a gap between:

* Notebook-based workflows (e.g., Python/R notebooks)
* SQL-based querying tools
* Legacy statistical software (e.g., Stata/SAS)

Specifically, the tool aims to:

* Enable **fast, iterative EDA in a terminal**
* Provide **concise, expressive commands** for common statistical tasks
* Support **modern data formats and large datasets**
* Offer a **reproducible, scriptable workflow**

---

## 3. Problem / Need Analysis

### 3.1 Limitations of Existing Tools

#### Notebooks (Python/R)

* Stateful and error-prone (hidden state issues)
* Verbose for simple EDA tasks
* Poor ergonomics for rapid command iteration
* Not ideal for terminal-centric users

#### SQL Tools

* Strong for querying, weak for statistical summaries
* Verbose for common EDA operations (e.g., distributions, missingness)
* Lack expressive statistical commands

#### Legacy Statistical Software

* Strong command ergonomics
* Weak support for:

  * Parquet / Arrow
  * Lazy / out-of-core execution
  * Modern data ecosystems
* Often proprietary or expensive

#### Pandas / Polars APIs

* Powerful but:

  * Verbose for routine tasks
  * Less intuitive for non-programmers
  * Not optimized for quick exploratory workflows

---

### 3.2 Emerging Needs

Modern data workflows increasingly require:

* Native support for **columnar formats (Parquet, Feather)**
* Read support for **Stata `.dta` files**, including remote HTTP/HTTPS sources
* Ability to work with **datasets larger than memory**
* Integration with **data lake / object storage**
* Faster iteration cycles for **EDA and validation**
* More **reproducible, scriptable CLI workflows**

This project addresses these needs directly.

---

## 4. Target Users

### Primary User Groups

1. **Statisticians and analysts**

   * Familiar with command-based tools (Stata, SAS)
   * Need efficient descriptive analysis workflows

2. **Data scientists (CLI-oriented)**

   * Prefer terminal over notebooks
   * Want fast iteration and reproducibility

3. **Data analysts working with Parquet/lake data**

   * Need lightweight local exploration tools
   * Avoid heavy infrastructure (Spark, etc.)

4. **R users (EDA-first workflows)**

   * Strong statistical background
   * Friction with large datasets and I/O

5. **Engineers debugging data**

   * Need quick inspection tools
   * Prefer minimal setup and fast feedback

---

## 5. Scope

### 5.1 In Scope (MVP)

#### Data I/O

* Read/write:

  * Parquet (primary)
  * Stata `.dta` (read)
  * CSV
  * Feather / Arrow
* Lazy and eager loading modes

#### Core EDA Commands

* `describe`
* `summarize`
* `codebook`
* `tabulate`
* `count`
* `head`, `tail`

#### Data Manipulation

* `keep`, `drop`
* `select`
* `generate`, `replace`
* `rename`
* `recode`

#### Group Operations

* `by:`
* `collapse`
* cross-tabulations

#### SQL Integration

* ANSI-style SQL queries
* Access to active dataset and named tables

#### Visualization

* Basic plots:

  * histogram
  * scatter
  * bar charts
* Output to artifact directory (PNG/SVG)
* Auto-open via system viewer

#### CLI UX

* Interactive shell
* Syntax highlighting
* Context-aware autocomplete
* Command history
* Script execution (`.do`-like files)

---

### 5.2 Out of Scope (Initial)

* Advanced statistical modeling
* Machine learning pipelines
* Distributed compute (Spark-scale)
* GUI or notebook interfaces
* Collaborative multi-user features

---

## 6. System Architecture

### 6.1 High-Level Components

```text
[ CLI Shell ]
    ↓
[ Command Parser / Language Layer ]
    ↓
[ Execution Engine ]
    ↓
[ Data Backend (DuckDB / Polars / Arrow) ]
```

---

### 6.2 Technology Stack

#### CLI Layer

* `prompt_toolkit`

  * syntax highlighting
  * autocomplete
  * history

#### Language / Parsing

* Custom command grammar
* Expression parser (lightweight, extensible)

#### Execution Backend

* DuckDB (SQL + lazy execution)
* Polars (fast DataFrame operations)
* Apache Arrow (data interchange)

#### Optional Integration

* R via `rpy2` (future phase)

#### Layered Product Direction

The product-defining core is terminal EDA: loading, inspection, transformation, joins/reshape,
scripting, SQL, deterministic output, and execution transparency. Conventional statistics form a
second capability layer. Bayesian, spatial, R, and ML integrations are specialized capabilities
that must not be required to install or start the core workflow.

These are dependency and product boundaries first. Whether they become optional dependency groups
or separate distributions must be decided from installation-size, startup-latency, portability,
and maintenance evidence. Until the public-preview readiness gate is met, correctness and workflow
depth take priority over new estimator families.

#### Packaging / Dev

* Python + `uv`

---

## 7. Command Language Design

### 7.1 Philosophy

* Inspired by Stata, but not constrained by it
* Concise, readable, composable
* Minimal boilerplate
* Predictable behavior

---

### 7.2 Example Commands

```stata
use patients.parquet

describe
summarize age bmi
tabulate sex outcome, row col

keep if age >= 18
generate log_cost = log(cost)

collapse mean bmi cost, by(sex)
```

---

### 7.3 SQL Integration

```stata
sql select sex, avg(bmi) as mean_bmi
    from active
    group by sex

sql """
select outcome, count(*) as n
from active
where age >= 18
group by outcome
""" into summary
```

---

## 8. Visualization Design

### 8.1 Output Model

* All plots are saved as artifacts by default:

```text
artifacts/plots/
```

Example:

```text
histogram_age_20260502_143012.png
```

---

### 8.2 Behavior

Default:

```stata
histogram age
```

* Save to artifact directory
* Open with system viewer
* Print file path

Explicit:

```stata
histogram age, saving(figures/age_hist.svg)
```

---

### 8.3 Configuration

```stata
set graph_format svg
set artifact_dir artifacts/
set graph_open off
```

---

## 9. Initial UX Sketches

### 9.1 Interactive Session

```text
> use patients.parquet
Loaded: patients.parquet (lazy)

> summarize age bmi
---------------------------------
Variable   Mean    Std Dev   Min   Max
---------------------------------
age        52.3    14.2      18    89
bmi        27.1    5.3       16    42

> tabulate sex outcome, row
```

---

### 9.2 Autocomplete Behavior

```text
> summarize <TAB>
age  bmi  glucose  outcome

> tabulate sex outcome, <TAB>
row  col  missing
```

---

### 9.3 Plot Output

```text
> histogram age
Saved: artifacts/plots/histogram_age_20260502_143012.png
Opened with default viewer.
```

---

### 9.4 SQL Workflow

```text
> sql select * from active limit 5
Preview (5 rows)

> sql select * from active where age > 50 into older
Table 'older' created

> use older
```

---

## 10. Key Differentiators

1. **Command-driven EDA workflow**
2. **Native Parquet and Arrow support**
3. **Lazy execution for large datasets**
4. **Integrated SQL + statistical commands**
5. **Terminal-native UX (autocomplete, highlighting)**
6. **Artifact-based visualization model**

---

## 11. Future Directions

* Extended statistical functions
* Integration with R libraries
* Interactive HTML visualizations
* Plugin system for custom commands
* Remote data access (S3, databases)
* Session persistence and reproducibility enhancements

---

## 12. Summary

This project aims to deliver a **modern, lightweight, and expressive EDA environment** that:

* Feels familiar to statisticians
* Feels fast to engineers
* Scales to modern datasets
* Lives comfortably in the terminal

It occupies a unique and currently underserved space at the intersection of:

**statistical ergonomics + modern data infrastructure + CLI-native workflows**

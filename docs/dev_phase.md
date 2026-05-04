---
title: "Development Roadmap"
author: "Sae-Hwan Park"
date: 2026-05-02
description: "a high-level phased plan that balances architecture discipline + rapid usability validation."
---

# Development Roadmap

## Phase 0 — Product Definition & Guardrails

**Goal:** Prevent scope creep and lock core principles.

### Deliverables

* Clear positioning statement
* Non-goals (explicitly written)
* Initial command set (10–15 commands max)
* Naming decision (project + CLI command)

### Key Decisions

* “Stata-inspired, not compatible”
* Single active dataset (for MVP)
* DuckDB as primary execution engine
* Parquet-first design

### Output

* Short design doc (what you already started)
* Command glossary (v0)

---

## Phase 1 — Core Skeleton (Vertical Slice)

**Goal:** End-to-end working prototype, even if minimal.

This is the most important phase.

### Features

* CLI shell (basic)
* `use` command (load Parquet)
* `describe`
* `summarize`
* minimal parser (command + args)

### Architecture (minimal but clean)

```text
CLI → Parser → Executor → DuckDB
```

### Example milestone

```stata
use data.parquet
summarize age
```

### Constraints

* No autocomplete yet
* No visualization yet
* No fancy parsing

### Success Criteria

* You can load a dataset and run 2–3 commands reliably

---

## Phase 2 — Command Language & Parser

**Goal:** Make the system feel like a real tool.

### Features

* Command grammar:

  * `command varlist, options`
  * `if` conditions
* Expression parsing (`generate`, `keep if`)
* Error handling with useful messages

### Example

```stata
keep if age >= 18
generate log_cost = log(cost)
```

### Technical Focus

* Build a simple but extensible parser

  * Avoid overengineering (no full compiler needed)
* Define AST-like internal representation

### Success Criteria

* Users can write small scripts without friction

---

## Phase 3 — Core EDA Functionality

**Goal:** Reach “actually useful” status.

### Features

#### Inspection

* `describe`
* `summarize`
* `codebook`
* `count`

#### Transformation

* `keep`, `drop`
* `select`
* `rename`
* `generate`, `replace`

#### Grouping

* `by:`
* `collapse`
* `tabulate`

### Backend Work

* Map commands → DuckDB queries or Polars ops
* Ensure lazy execution works transparently

### Success Criteria

* Can do full first-pass EDA without leaving the tool

---

## Phase 4 — SQL Integration

**Goal:** Add power without expanding command surface too much.

### Features

* `sql` command (single-line + multiline)
* Active dataset exposed as `active`
* `into <table>` support

### Example

```stata
sql select sex, avg(bmi) from active group by sex
```

### Design Principle

* SQL is an **escape hatch**, not primary interface

### Success Criteria

* Users can solve edge cases without waiting for new commands

---

## Phase 5 — CLI UX (Major Differentiator)

**Goal:** Make the tool feel modern and pleasant.

### Features (via `prompt_toolkit`)

* Syntax highlighting
* Context-aware autocomplete:

  * commands
  * column names
  * options
* Command history
* Inline suggestions

### Example

```text
summarize <TAB> → age bmi glucose
```

### Important

This phase significantly increases perceived quality.

### Success Criteria

* Feels faster and more intuitive than raw CLI tools

---

## Phase 6 — Visualization System

**Goal:** Lightweight but useful plotting.

### Features

* `histogram`, `scatter`, `bar`
* Artifact-based output:

  * default `artifacts/plots/`
* Auto-open behavior
* `saving()` option

### Example

```stata
histogram age
scatter bmi age, saving(figures/bmi_age.svg)
```

### Backend

* Start with:

  * Altair (preferred)
  * or matplotlib fallback

### Success Criteria

* Users can visually inspect distributions quickly

---

## Phase 7 — Lazy Execution & Performance Optimization

**Goal:** Make large data workflows smooth.

### Features

* Explicit `lazy` mode in `use`
* Pushdown operations (filter, select, groupby)
* Avoid unnecessary materialization

### Backend Work

* Tight DuckDB integration
* Optional Polars lazy pipelines

### Success Criteria

* Handles datasets larger than memory without user friction

---

## Phase 8 — Scripting & Reproducibility

**Goal:** Make it usable in real workflows.

### Features

* Script execution from file:
  * `tabdat -f analysis.td`
  * `tabdat analysis.td`
  * interactive `run analysis.td`
* Script parser layer for command sequences and future script-level constructs.
  * Keep row-level `if` expressions distinct from future script-level `if` / `else`.
  * Reserve AST space for later loops, macro substitution, and error-control forms without
    forcing those constructs into the first slice.
* Logging and deterministic batch output.
* Golden-output tests for complete mini sessions.
* Reproducibility metadata in script runs, including TabDat version, Python version, backend
  engine, and relevant configuration.
* Lazy-mode honesty pass:
  * avoid load-time full counts for lazy datasets unless the user explicitly requests them
  * document which commands preserve lazy scans and which materialize intermediate results
* Polars engine decision:
  * either hide Polars from user-facing lazy options until it has real execution coverage
  * or mark it experimental in command help and script metadata
* Dogfood gate: complete one public-dataset EDA using only `tabdat` before expanding the
  command surface beyond scripting support.

### Example

```stata
run analysis.td
```

### Success Criteria

* Users can replace notebook EDA with scripts for first-pass analysis.
* The same script run against the same input produces deterministic terminal output and
  artifacts, except where timestamps or user-selected output paths are explicit.
* Full-session tests cover representative `use`, inspect, transform, SQL, plot, and script
  execution flows.

---

## Phase 9 — Configuration & Environment

**Goal:** Make behavior predictable and customizable.

### Features

* `set` commands:

```stata
set graph_format svg
set artifact_dir artifacts/
set graph_open off
```

* Config file support
* `save` / `export` command contract for writing session-local transformations to durable
  files.
* Plot artifact naming policy for reproducible scripts and interactive reruns.

### Success Criteria

* Tool behaves consistently across environments
* Users can persist transformed datasets without leaving the tool.

---

## Phase 10 — Extensions & Ecosystem (Later)

**Goal:** Expand capability without bloating core.

### Possible Additions

* R integration (`rpy2`)
* Plugin system
* Remote data (S3, DB connections)
* Interactive HTML plots
* Advanced stats modules
* Lightweight named table registry that augments, but does not replace, the single active
  dataset model.
* Executor dispatch refactor if command handlers or script meta-commands make the central
  dispatcher difficult to maintain.
* More specific error subclasses for context-sensitive CLI and script diagnostics.

---

# Development Strategy (Critical)

## 1. Build Vertical, Not Horizontal

Instead of:

```text
implement all commands → then UX → then performance
```

Do:

```text
small end-to-end slice → refine → expand
```

---

## 2. Dogfood Early

Use the tool for your own EDA as soon as Phase 2–3.

You’ll quickly discover:

* missing commands
* awkward syntax
* performance issues

---

## 3. Keep Command Surface Small Initially

Avoid:

```text
50 commands partially implemented
```

Prefer:

```text
10 commands extremely solid
```

---

## 4. Treat UX as Core, Not Polish

Autocomplete + syntax highlighting are not “nice-to-have.”

They are part of the **value proposition**.

---

## 5. Delay R Integration

It’s tempting, but:

* adds packaging complexity
* introduces cross-language edge cases

Add only after core is stable.

---

# Suggested Milestone Timeline (Rough)

```text
Phase 1–2   → 2–3 weeks   (working prototype)
Phase 3     → 2–4 weeks   (usable EDA tool)
Phase 4–5   → 2–3 weeks   (power + UX)
Phase 6     → 1–2 weeks   (visualization)
Phase 7+    → ongoing     (optimization + expansion)
```

---

# Final Takeaway

The success of this project depends on:

* **fast feedback loops**
* **tight UX focus**
* **resisting overengineering early**

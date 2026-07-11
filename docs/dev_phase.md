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

## Phase 10 — Execution & State Foundations

**Goal:** Strengthen execution boundaries before analytical expansion.

### Coverage

* Lightweight named table registry that augments, but does not replace, the single active
  dataset model
* Executor dispatch refactor if command handlers or script meta-commands make the central
  dispatcher difficult to maintain
* More specific error subclasses for context-sensitive CLI and script diagnostics
* Honest lazy/materialization contract and deeper Polars-boundary decisions

### Non-goals

* No broad analytical command expansion yet
* No plugin or R integration yet

### Exit Gate

* Multi-table session state, execution dispatch, and lazy-mode boundaries are stable enough to
  support later estimation commands without immediate redesign

---

## Phase 11 — Data Workflow & Reproducibility Primitives

**Goal:** Support estimation-ready data workflows inside `tabdat`.

### Coverage

* Join / merge-style commands for multi-table workflows
* Append / stack and reshape wide/long support
* Panel identifier handling and related dataset metadata
* Script-level reproducibility primitives such as seeding, reusable variables/macros, and
  minimal control-flow constructs
* Remote data access in the narrowest useful form, starting with DuckDB-friendly sources such
  as S3/object-store Parquet and DB connections

### Non-goals

* No general plugin system
* No large analytical model catalog yet

### Exit Gate

* Users can build reproducible estimation-ready datasets without leaving `tabdat`

---

## Phase 12 — Estimation Substrate

**Status:** Implemented.

**Goal:** Build reusable estimation engines and statistical primitives.

### Coverage

* Statistical primitives: distributions, moments, covariance infrastructure
* Simulation and resampling utilities, including bootstrap support
* Reusable least-squares, generic MLE, and GMM estimation interfaces
* Shared internal result contract for coefficients, standard errors, diagnostics, predictions,
  and model metadata

### Non-goals

* No large family of end-user model commands yet
* No late-stage ecosystem extensions yet

### Exit Gate

* Core estimators can be implemented as thin command layers over shared estimation machinery

---

## Phase 13+ — Statistical/Econometric Library Policy

**Goal:** Keep econometric command development pragmatic and reliable by defaulting to mature
libraries instead of bespoke estimators.

### Priority Order

1. Well-established Python libraries when the method exists directly or can be composed with
   limited orchestration.
2. Well-established R libraries via `rpy2` adapters when Python coverage is missing or the Python
   path is workaround-heavy.
3. Focused lower-level implementations over `numpy`/`scipy` only when neither higher-level route
   is acceptable.

### Constraint

* Command handlers should stay thin and map library results into the shared Phase 12 estimation
  result contract.

---

## Phase 13 — Core Linear Econometrics

**Goal:** Deliver the standard cross-sectional linear analysis workflow.

### Coverage

* OLS and weighted least squares
* Robust and cluster-robust inference
* Generalized least squares
* Prediction, fitted values, and residual workflows
* Linear-model diagnostics
* Interactive HTML output for model inspection only if it materially improves regression
  diagnostics over artifact-based static output

### Non-goals

* No IV, panel, or nonlinear models yet

### Library Strategy (Priority Order)

1. Python first: `statsmodels` for OLS/WLS/GLS, robust and cluster-robust covariance,
   prediction/fitted-value workflows, and standard linear diagnostics.
2. R fallback via `rpy2`: `fixest` or `estimatr` for inference variants not covered cleanly by
   Python.
3. Lower-level fallback: targeted `numpy`/`scipy` linear algebra and inference helpers only when
   the first two layers cannot meet the command contract.

### Exit Gate

* Linear econometric analysis is solid enough to dogfood on real analytical projects

---

## Phase 14 — Endogeneity & Panel Foundations

**Goal:** Cover the standard linear microeconometrics baseline.

### Coverage

* Instrumental variables and 2SLS
* Weak-instrument and overidentification diagnostics
* Control-function entry points where they fit the linear workflow
* Panel indexing semantics and within/between transformations
* Fixed effects, random effects, and Hausman-style comparisons

### Non-goals

* No nonlinear or limited dependent variable families yet

### Library Strategy (Priority Order)

1. Python first: `linearmodels` for IV/2SLS, IV-GMM, and panel FE/RE workflows; use
   `statsmodels` diagnostics as needed.
2. R fallback via `rpy2`: `AER` (`ivreg`), `plm`, and `fixest` for panel/IV coverage gaps.
3. Lower-level fallback: targeted `numpy`/`scipy` implementations on top of the shared GMM
   substrate for missing pieces only.

### Exit Gate

* The tool supports the common cross-sectional and panel linear identification workflows

---

## Phase 15 — Nonlinear Estimation Core

**Goal:** Extend the estimation stack beyond linear models.

### Coverage

* Binary choice models such as logit and probit
* Marginal effects and nonlinear prediction workflows
* General nonlinear regression
* Limited dependent variable models such as Tobit, truncated regression, and sample selection

### Non-goals

* No broad discrete-choice tree or mixture-model catalog yet

### Library Strategy (Priority Order)

1. Python first: `statsmodels` for logit/probit, marginal effects, and core nonlinear likelihood
   workflows.
2. R fallback via `rpy2`: `sampleSelection`, `censReg`, and `truncreg` for Heckman-style,
   censored, and truncated model coverage.
3. Lower-level fallback: targeted `scipy.optimize` + `numpy` MLE implementations only when needed
   to satisfy command contracts.

### Exit Gate

* Nonlinear cross-sectional estimation is a first-class workflow built on the shared MLE layer

---

## Phase 16 — Specialized Likelihood Models

**Goal:** Broaden the applied-micro model catalog.

### Coverage

* Discrete-choice systems: multinomial, conditional, and nested logit
* Count models: Poisson, negative binomial, and overdispersion-aware workflows
* Mixture, hurdle, and zero-inflated models
* Duration and survival models

### Non-goals

* No advanced panel GMM, causal, or semiparametric expansion yet

### Library Strategy (Priority Order)

1. Python first: `statsmodels` for multinomial/count/zero-inflated families and `lifelines` for
   duration/survival workflows.
2. R fallback via `rpy2`: `mlogit`, `glmmTMB`, and `survival` for model families not covered
   cleanly in Python.
3. Lower-level fallback: targeted `scipy.optimize` + `numpy` likelihood implementations only when
   the first two layers are insufficient.

### Exit Gate

* The core applied-micro model families are broadly covered without bespoke execution stacks for
  each family

---

## Phase 17 — Advanced Empirical Methods

**Goal:** Add the methods that depend on a mature estimation base.

### Coverage

* Dynamic and advanced panel GMM workflows
* Nonlinear panel models
* Quantile and distributional methods
* Semiparametric and nonparametric methods
* Causal inference workflows, including treatment-effects, matching/weighting, and endogenous
  treatment cases

### Non-goals

* No broad plugin, ML, Bayesian, or spatial ecosystem expansion yet

### Library Strategy (Priority Order)

1. Python first: `linearmodels`/`statsmodels` where available for panel-GMM, quantile, and
   semiparametric building blocks.
2. R fallback via `rpy2`: `fixest`, `did`, `MatchIt`, `Synth`, and `quantreg` for mature causal
   and distributional workflows.
3. Lower-level fallback: targeted `numpy`/`scipy` implementations only when the first two layers
   cannot satisfy method requirements.

### Exit Gate

* Research-grade empirical methods are available without destabilizing the simpler command
  surface

---

## Phase 18 — Ecosystem & Extension Layer

**Goal:** Expose stable extension points after the analytical core settles.

### Coverage

* Plugin system built on stable command and result interfaces
* Hardened `rpy2` interoperability boundary for targeted R-package adapters introduced in earlier
  phases
* Broader remote connectors beyond the first DuckDB-friendly sources

### Non-goals

* No requirement to expand core estimators while extension interfaces are still settling

### Library Strategy (Priority Order)

1. Python first: stabilize adapter layers for adopted Python libraries (`statsmodels`,
   `linearmodels`, `lifelines`, and related dependencies).
2. R fallback via `rpy2`: standardize package curation and adapter contracts for approved R
   dependencies (`fixest`, `plm`, `lme4`, and related phase-approved packages).
3. Lower-level fallback: keep custom numerical code limited to compatibility glue and
   performance-critical kernels.

### Exit Gate

* External integrations build on stable analytical APIs rather than forcing core redesign

---

## Phase 19 — Modern Extensions

**Goal:** Add broad methods that should remain explicitly late-stage.

### Coverage

* Machine learning integration
* Bayesian workflows
* Spatial models

### Non-goals

* No pressure to make these methods define the core product architecture

### Library Strategy (Priority Order)

1. Python first: `scikit-learn` for ML workflows, `pymc`/`bambi` for Bayesian workflows, and
   `pysal` (`spreg`) for spatial econometrics.
2. R fallback via `rpy2`: `brms`/`rstanarm` and `spdep`/`spatialreg` where R has stronger mature
   coverage.
3. Lower-level fallback: narrow `numpy`/`scipy` custom implementations only when no mature backend
   fits the required method.

### Exit Gate

* Modern extensions are available as additions to a stable econometrics-first system

---

## Phase 24 — Product-Center Stabilization & Public Preview

**Goal:** Validate TabDat's core terminal-EDA thesis and reduce installation, semantic, and trust
risk before resuming breadth expansion.

### Priority Order

1. Publish and benchmark one unmistakable Parquet-first journey from lazy load through
   deterministic script replay and export.
2. Specify cross-command identifiers, missingness, coercion, ordering, overwrite, randomness,
   estimation-sample, error, and exit semantics.
3. Expose backend, source, lazy/materialized state, operation lineage, known row counts,
   materialization reasons, and estimation sample.
4. Add stable JSON/JSONL output, structured discovery, dry-run/explain, and repair diagnostics.
5. Expand golden and differential testing and publish a trusted-reference statistical matrix.
6. Measure install/startup costs and formalize core, stats, and specialized dependency capabilities.
7. Resolve naming/versioning, separate architecture/capabilities/history/ADRs, test clean installs
   and portability, and gather external workflow feedback.

### Sequencing Constraint

Net-new estimator families and broad integrations remain queued until this phase exits. Existing
estimators remain supported and may receive correctness, compatibility, and documentation fixes.
Packaging must follow measurements and an ADR; conceptual layers do not by themselves require
multiple repositories or distributions.

### Exit Gate

* A clean core install completes the canonical EDA workflow without R, Bayesian, spatial, or ML runtimes.
* Interactive and scripted runs are deterministic and have equivalent state transitions.
* Users can inspect execution and materialization boundaries without causing materialization.
* Stable language and machine-output contracts are documented and covered by focused tests.
* Shared backend/eager/lazy behavior has differential coverage.
* Statistical commands have a published support matrix and reference-validation status.
* Naming, versioning, dependency layering, and documentation ownership are recorded decisions.
* At least one external-user feedback round has been captured and triaged.

### Non-goals

* Removing completed estimator surfaces solely to simplify the roadmap
* Adding another estimator as evidence of product readiness
* Splitting packages before dependency and startup measurements justify it

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

## 5. Use R Selectively, Not Broadly

R integration remains useful, but should stay scoped:

* targeted `rpy2` adapters are allowed from Phase 13 onward when Python coverage is missing or
  workaround-heavy
* broad R-surface expansion should wait until interoperability and packaging boundaries are stable

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

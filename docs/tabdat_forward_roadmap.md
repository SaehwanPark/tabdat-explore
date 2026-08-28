---
title: "TabDat Forward Roadmap"
author: "Sae-Hwan Park"
date: 2026-08-27
status: "Active"
roadmap_scope: "Current and forward-looking development priorities"
supersedes_on_conflict: "docs/dev_phase.md"
precedence: "When this roadmap conflicts with docs/dev_phase.md, this roadmap takes priority for all work from 2026-08-27 onward. docs/dev_phase.md remains historical context unless explicitly reconciled."
---

# TabDat Forward Roadmap

## 1. Purpose

This roadmap defines TabDat's development priorities from the current project state forward.

TabDat has already demonstrated that its core product idea works:

> A fast, reproducible, terminal-native statistical EDA environment for modern tabular data, with Stata-inspired ergonomics and a clean machine interface.

The primary challenge is no longer proving that the command language or statistical surface can expand. The priority is now to make the product:

- trustworthy;
- semantically stable;
- architecturally maintainable;
- lightweight enough for routine use;
- installable outside the source repository;
- distributable as a normal command-line application;
- validated against trusted statistical references;
- usable by both humans and automated callers;
- ready for external users without requiring repository-specific knowledge.

This roadmap intentionally prioritizes product stabilization, deployment, trust, and architecture over additional estimator breadth.

---

# 2. Roadmap Authority and Scope Control

## 2.1 Precedence

This document is the active forward roadmap.

- [ ] Treat this file as the primary planning authority for all new work.
- [ ] When this file and `docs/dev_phase.md` disagree, follow this file.
- [ ] Preserve `docs/dev_phase.md` as historical context unless a later task explicitly reconciles or archives it.
- [ ] Update this roadmap whenever priorities, sequencing, acceptance criteria, or deployment decisions materially change.
- [ ] Record major irreversible architecture or packaging decisions in ADRs rather than only editing roadmap prose.

## 2.2 Development Freeze on Breadth

Until the stabilization and public-preview gates defined below are complete:

- [ ] Do not add new estimator families.
- [ ] Do not add broad new data-source integrations.
- [ ] Do not start GUI or notebook interfaces.
- [ ] Do not pursue broad Stata compatibility.
- [ ] Do not add distributed-compute backends.
- [ ] Do not expand R integration beyond maintenance of already-supported capabilities.
- [ ] Do not split the project into multiple repositories solely for conceptual cleanliness.
- [ ] Allow correctness fixes, compatibility fixes, documentation fixes, performance work, and bounded improvements to existing commands.

Any proposed exception must answer all of the following:

- [ ] What concrete user problem cannot be solved with the existing surface?
- [ ] Why should this work precede stabilization or deployment?
- [ ] What maintenance burden does it add?
- [ ] What existing roadmap work will be delayed?
- [ ] Has the exception been explicitly recorded in an ADR or roadmap update?

---

# 3. Product North Star

A successful normal-user workflow should eventually be:

```bash
$ curl -LsSf https://tabdat.dev/install.sh | sh

$ cd ~/research/my-project
$ tabdat

tabdat> use data/analytic.parquet, lazy
tabdat> describe
tabdat> summarize age bmi
tabdat> by treatment: summarize outcome
tabdat> regress outcome treatment age bmi
tabdat> export results/analytic.parquet
```

The user should not need to:

- clone the TabDat repository;
- activate a TabDat development virtual environment;
- run `uv run tabdat`;
- understand TabDat's internal Python package layout;
- install unrelated Bayesian, spatial, ML, or R ecosystems to perform core EDA;
- know which backend is used unless they choose to inspect it.

A successful automation workflow should use the same language and semantics:

```bash
tabdat --json -c "use data.parquet" -c "summarize age bmi"
```

Human and machine interfaces must share the same execution semantics rather than evolving into separate products.

---

# 4. Always-On Engineering Invariants

These requirements apply across every phase.

## 4.1 Quality Gates

Before merging user-visible behavior changes:

- [ ] `uv run pytest` passes.
- [ ] `uv run basedpyright` passes.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run python scripts/check_docs_alignment.py` passes.
- [ ] Relevant focused regression tests are added or updated.
- [ ] User-visible command behavior is reflected in in-app help where applicable.
- [ ] Machine-readable command/help metadata is updated where applicable.
- [ ] Error behavior is tested, not only success behavior.

For release candidates:

- [ ] Run the complete integrated E2E suite.
- [ ] Run the canonical Parquet workflow at least twice.
- [ ] Verify deterministic transcript and output equality where the command contract requires determinism.
- [ ] Test from a clean environment rather than only from the developer checkout.
- [ ] Record validation results in a release or run report.

## 4.2 Architecture Invariants

- [ ] Preserve a clear language → execution → backend dependency direction.
- [ ] Core EDA must not require Bayesian, spatial, ML, or R imports.
- [ ] Specialized capabilities must fail at their command boundary with actionable guidance when unavailable.
- [ ] Command parsing must not silently depend on installed statistical backends.
- [ ] Dataset mutations must remain atomic on failure.
- [ ] Estimation-family state must not leak across incompatible post-estimation commands.
- [ ] Human-readable and JSON behavior must derive from the same underlying command/result semantics.

## 4.3 Documentation Invariants

- [ ] `README.md` remains focused on normal-user onboarding.
- [ ] `docs/user-guide.md` owns workflow-oriented behavior.
- [ ] `docs/command-reference.md` owns the command inventory.
- [ ] `ARCHITECTURE.md` owns durable component boundaries and invariants.
- [ ] `CHANGELOG.md` owns historical release changes.
- [ ] ADRs own major architectural and packaging decisions.
- [ ] This roadmap owns forward priority and sequencing.
- [ ] Avoid duplicating the same normative contract across multiple documents without an explicit source of truth.

---

# 5. Phase 24A — Finish Product-Center Stabilization

## Goal

Complete the remaining semantic and transparency work needed for TabDat to behave like a predictable language rather than a collection of commands.

## 5.1 Language Semantics

### Identifiers

- [ ] Document unquoted identifier rules.
- [ ] Document quoted identifier rules.
- [ ] Define and test case behavior.
- [ ] Define reserved-name behavior.
- [ ] Define collision behavior for generated variables.
- [ ] Define overwrite behavior for mutating commands.
- [ ] Confirm failed identifier operations leave the active dataset unchanged.

### Missingness

- [ ] Define missing-value predicates.
- [ ] Define equality/inequality semantics involving missing values.
- [ ] Define missing propagation through arithmetic.
- [ ] Define missing behavior in grouped operations.
- [ ] Define missing category placement in tabulations and plots.
- [ ] Add cross-engine tests for all supported missingness rules.

### Coercion and Arithmetic

- [ ] Document numeric-family compatibility.
- [ ] Document string/numeric mixed-domain failures.
- [ ] Define integer result-width behavior.
- [ ] Define overflow behavior.
- [ ] Define non-finite result handling.
- [ ] Verify arithmetic failures are deterministic across eager/lazy boundaries.
- [ ] Verify failed transformations are atomic.

### Ordering

- [ ] Define active row-order guarantees.
- [ ] Define grouped-result ordering.
- [ ] Define categorical ordering.
- [ ] Define `append` ordering.
- [ ] Define `join` ordering.
- [ ] Define `reshape` ordering.
- [ ] Define named-table reactivation ordering.
- [ ] Document when SQL output is ordered only if `ORDER BY` is present.
- [ ] Add differential eager/lazy ordering tests.

## 5.2 Estimation Semantics

- [ ] Define estimation-sample construction.
- [ ] Define missing-row exclusion rules for all existing estimator families.
- [ ] Surface estimation sample size consistently.
- [ ] Define how latest-model state is invalidated.
- [ ] Define random seed precedence.
- [ ] Define deterministic behavior for seeded commands.
- [ ] Define behavior for unseeded stochastic commands.
- [ ] Standardize convergence/failure reporting.
- [ ] Standardize successful-with-warning behavior where supported.
- [ ] Standardize command exit status for estimation failures.

## 5.3 Execution Transparency

`status` and related machine interfaces should make important hidden state inspectable.

- [ ] Show active source.
- [ ] Show active backend.
- [ ] Show eager/lazy state.
- [ ] Show lazy engine.
- [ ] Show known/unknown row count.
- [ ] Show last successful command.
- [ ] Show most recent materialization reason.
- [ ] Show panel metadata when set.
- [ ] Show latest estimation family and estimation sample metadata.
- [ ] Ensure inspection commands do not themselves force materialization unless explicitly documented.
- [ ] Add JSON representation for the same state.

## 5.4 Machine Interface

- [ ] Stabilize JSON success-envelope schema.
- [ ] Stabilize JSON error-envelope schema.
- [ ] Stabilize command discovery schema.
- [ ] Stabilize structured help retrieval.
- [ ] Stabilize syntax-preview behavior.
- [ ] Stabilize declared command-effect metadata.
- [ ] Stabilize command-schema discovery.
- [ ] Add schema-version field or equivalent compatibility mechanism.
- [ ] Define backward-compatibility policy for machine-readable fields.
- [ ] Ensure JSON output never requires scraping human terminal output.

## Exit Gate

Phase 24A is complete only when:

- [ ] Core language semantics are documented and covered by focused tests.
- [ ] Canonical eager and lazy workflows agree where semantics require agreement.
- [ ] Dataset-changing failures are atomic.
- [ ] Estimation-sample and randomness rules are documented.
- [ ] `status` exposes the important execution state without unexpectedly materializing data.
- [ ] JSON schemas are stable enough to support downstream automation.
- [ ] No known P0/P1 semantic ambiguity remains open.

---

# 6. Phase 24B — Modularize the Architecture and Capability Boundaries

## Goal

Make the physical code structure match the intended architecture before public distribution hardens current coupling.

The current large parser, executor, backend, and test modules should be decomposed without changing public behavior.

## 6.1 Establish Target Module Boundaries

Target conceptual layout:

```text
tabdat/
  language/
    parser/
    expressions/
    syntax/

  commands/
    data/
    transform/
    summarize/
    visualize/
    stats/
    econometrics/
    ml/
    bayes/
    spatial/

  execution/
    dispatcher/
    context/
    state/
    capabilities/

  backend/
    duckdb/
    polars/

  reporting/
  help/
```

This structure is illustrative; exact paths should be chosen through implementation experience and ADRs.

Checklist:

- [ ] Write an architecture ADR for command/handler registration.
- [ ] Write an architecture ADR for capability/dependency layering.
- [ ] Identify all responsibilities currently concentrated in `executor.py`.
- [ ] Identify all responsibilities currently concentrated in `parser.py`.
- [ ] Identify all responsibilities currently concentrated in `backend.py`.
- [ ] Extract modules incrementally with no user-visible behavior changes.
- [ ] Keep imports acyclic and directionally consistent.
- [ ] Preserve 2-space formatting and type-safety requirements.

## 6.2 Command Registration

Create a single durable registration boundary tying together command metadata.

Desired conceptual mapping:

```text
command name
  → parser/schema
  → command type
  → execution handler
  → help topic
  → declared effects
  → optional capability requirement
```

- [ ] Inventory current duplicated command registries.
- [ ] Define a typed registration contract.
- [ ] Migrate commands incrementally.
- [ ] Detect duplicate command registrations at startup/test time.
- [ ] Detect commands missing help metadata.
- [ ] Detect commands missing machine-readable metadata.
- [ ] Detect commands missing execution handlers.
- [ ] Keep parser-only discovery possible without initializing heavy capabilities.

## 6.3 Dependency Layering

Target conceptual capability layers:

```text
tabdat-core
  → conventional statistics
      → specialized capabilities
          bayes
          spatial
          ML
          R
```

- [ ] Measure current import graph.
- [ ] Identify specialized imports occurring during `import tabdat` or CLI startup.
- [ ] Move ML imports behind ML command boundaries.
- [ ] Move Bayesian imports behind Bayesian command boundaries.
- [ ] Move spatial imports behind spatial command boundaries.
- [ ] Move R/rpy2 imports behind R-dependent command boundaries.
- [ ] Confirm core EDA starts successfully when specialized libraries are absent.
- [ ] Add tests that intentionally run with specialized capabilities unavailable.
- [ ] Add actionable missing-capability errors.

## 6.4 Test Decomposition

- [ ] Split oversized test modules by command family or execution responsibility.
- [ ] Preserve integration-level tests that span modules.
- [ ] Add registry invariant tests.
- [ ] Add import-boundary tests.
- [ ] Add clean-core-environment tests.
- [ ] Keep canonical E2E scenarios independent from internal module layout.

## Exit Gate

Phase 24B is complete only when:

- [ ] Core startup does not import R, Bayesian, spatial, or ML stacks.
- [ ] Specialized features fail cleanly when optional capabilities are absent.
- [ ] Major command execution responsibilities are no longer concentrated in one monolithic executor module.
- [ ] Command metadata has one authoritative registration path or a documented equivalent.
- [ ] Existing test and E2E behavior remains unchanged.
- [ ] The architecture document reflects the implemented dependency graph rather than only the desired graph.

---

# 7. Phase 24C — Statistical Trust and Reference Validation

## Goal

Demonstrate that existing statistical functionality agrees with trusted reference implementations under explicitly defined conditions.

Software tests establish internal consistency. This phase establishes statistical trust.

## 7.1 Reference Validation Matrix

Create and maintain a tracked validation matrix with fields such as:

```text
command
estimator/mode
TabDat backend
reference implementation
reference version
dataset
coefficient tolerance
SE tolerance
diagnostic tolerance
prediction tolerance
known differences
validation status
last validated date
```

- [x] Define the matrix format.
- [x] Store it in a machine-readable form.
- [x] Render a human-readable version for documentation.
- [x] Include backend/library versions.
- [x] Include known intentional semantic differences.
- [x] Distinguish "implemented" from "reference validated".

## 7.2 Priority Validation Order

Validate the most common and foundational commands first.

### Tier 1

- [x] `regress`
- [x] robust covariance
- [x] clustered covariance
- [x] WLS/GLS where supported
- [x] `predict`
- [x] core `estat` diagnostics
- [x] `logit`
- [x] `probit`
- [x] `poisson`
- [x] `qreg`

### Tier 2

- [ ] `ivregress 2sls`
- [ ] `ivregress gmm`
- [ ] `xtreg fe`
- [ ] `xtreg re`
- [ ] `cfregress`
- [ ] `did`
- [ ] `xtabond`
- [ ] `xtlogit`

### Tier 3

- [ ] Tobit
- [ ] Heckman
- [ ] zero-inflated models
- [ ] survival models
- [ ] DML
- [ ] DR-DID
- [ ] regularized models
- [ ] Bayesian workflows
- [ ] spatial workflows

## 7.3 Differential Testing

Where feasible:

- [ ] Generate deterministic synthetic fixtures.
- [ ] Run TabDat and trusted references over the same data.
- [ ] Compare point estimates.
- [ ] Compare standard errors.
- [ ] Compare confidence intervals.
- [ ] Compare predictions.
- [ ] Compare observation/estimation sample counts.
- [ ] Compare post-estimation diagnostics.
- [ ] Document expected differences instead of weakening tolerances without explanation.

## 7.4 Trust Documentation

- [ ] Publish a statistical support/validation matrix.
- [ ] Mark commands with validation status.
- [ ] Document reference versions.
- [ ] Document unsupported or intentionally different semantics.
- [ ] Avoid claiming equivalence where only implementation testing exists.

## Exit Gate

Phase 24C is complete when:

- [ ] Every Tier 1 estimator has tracked reference validation.
- [ ] Every public estimator has an explicit validation status.
- [ ] No estimator is implicitly presented as reference-equivalent without evidence.
- [ ] Differential tests run in CI where licensing and environment constraints permit.
- [ ] Known statistical deviations are documented.

---

# 8. Phase 25 — Package and Installability Baseline

## Goal

Make TabDat a normal globally installable CLI before attempting native-style frozen binaries.

The user should be able to install TabDat once and run `tabdat` from arbitrary research directories.

## 8.1 Naming and Metadata

- [x] Decide final PyPI distribution name.
- [x] Remove `-dev` naming from production package metadata.
- [x] Confirm CLI command remains `tabdat`.
- [x] Define versioning policy.
- [x] Define supported Python versions.
- [x] Record Python-version decision in an ADR.
- [x] Confirm license metadata.
- [x] Add project URLs and issue tracker metadata.
- [x] Verify packaged help/resources are included in the wheel.

## 8.2 Build Validation

- [x] Build wheel from a clean checkout.
- [x] Build source distribution if supported.
- [x] Install wheel into a new isolated environment.
- [x] Run `tabdat --version`.
- [x] Run `tabdat -c "help summarize"`.
- [x] Run canonical EDA workflow from installed wheel.
- [x] Run from a directory outside the source repository.
- [x] Verify no accidental import from the repository checkout.
- [x] Verify resource paths do not depend on current working directory.

## 8.3 PyPI Publication

- [ ] Reserve/confirm final PyPI package name.
- [ ] Configure trusted publishing or equivalent secure release flow.
- [ ] Publish a pre-release candidate.
- [ ] Test installation from the public index.
- [ ] Publish stable release after acceptance criteria pass.
- [ ] Document upgrade and uninstall paths.

## 8.4 `uv tool` User Experience

Primary initial installation target:

```bash
uv tool install tabdat
```

- [ ] Verify `uv tool install tabdat` from PyPI.
- [ ] Verify `tabdat` is globally executable afterwards.
- [ ] Verify execution from multiple unrelated directories.
- [ ] Verify installation does not modify project-local environments.
- [ ] Document `uv tool upgrade`.
- [ ] Document uninstall procedure.
- [ ] Document optional capability installation once extras are finalized.

## 8.5 Dependency Profiles

Do not finalize extras before measurement, but establish measurable targets.

- [ ] Measure current clean install size.
- [ ] Measure dependency count.
- [ ] Measure CLI cold startup.
- [ ] Measure CLI warm startup.
- [ ] Measure import time.
- [ ] Record measurements on macOS and Linux at minimum.
- [ ] Define acceptable core-install thresholds in an ADR after measurement.
- [ ] Define optional dependency groups based on actual import/use boundaries.
- [ ] Verify core EDA does not require specialized stacks.

Potential target interface:

```bash
uv tool install tabdat
uv tool install "tabdat[stats]"
uv tool install "tabdat[ml]"
uv tool install "tabdat[bayes]"
uv tool install "tabdat[spatial]"
uv tool install "tabdat[r]"
uv tool install "tabdat[full]"
```

The exact groups remain subject to measurement and ADR decisions.

## Exit Gate

Phase 25 is complete when:

- [ ] A user can install TabDat from PyPI without cloning the repository.
- [ ] `tabdat` runs globally from arbitrary directories.
- [ ] A clean installed wheel completes the canonical workflow.
- [ ] Package/resource behavior is independent of source-checkout paths.
- [ ] Installation size and startup measurements are recorded.
- [ ] Core dependency boundaries are reflected in packaging.

---

# 9. Phase 26 — Release Automation and Continuous Delivery

## Goal

Make releases reproducible and testable rather than dependent on a developer workstation.

## 9.1 CI Baseline

- [x] Add GitHub Actions or equivalent CI.
- [x] Run unit tests on every pull request.
- [x] Run Ruff checks.
- [x] Run formatting checks.
- [x] Run basedpyright.
- [x] Run docs-alignment checks.
- [x] Test supported Python versions.
- [x] Test at least Linux and macOS.
- [ ] Add Windows where product support is intended.

## 9.2 Clean-Install CI

- [x] Build wheel in CI.
- [x] Install wheel into a clean environment.
- [x] Verify packaged help resources.
- [x] Run canonical workflow against installed artifact.
- [x] Ensure tests do not accidentally import the source tree.

## 9.3 Release Workflow

On a version tag:

- [x] Build artifacts.
- [x] Run release validation.
- [x] Generate checksums.
- [x] Publish GitHub Release.
- [ ] Publish PyPI release.
- [x] Attach validation metadata.
- [x] Fail the release if canonical workflow validation fails.

## 9.4 Release Documentation

- [ ] Document release procedure.
- [ ] Document rollback/yank procedure.
- [ ] Document version compatibility policy.
- [ ] Document release artifact provenance.
- [ ] Keep changelog entries tied to actual release versions.

## Exit Gate

Phase 26 is complete when:

- [ ] Stable releases can be produced from CI without manual local build steps.
- [ ] Every published release artifact passed clean-install E2E validation.
- [ ] Release provenance and checksums are available.
- [ ] Failed validation blocks publication.

---

# 10. Phase 27 — Frictionless Shell Installation

## Goal

Provide a one-command installation experience while still using the Python distribution underneath.

Target:

```bash
curl -LsSf https://tabdat.dev/install.sh | sh
```

## 10.1 Installer Contract

The installer should:

- [x] Detect supported OS.
- [x] Detect CPU architecture where relevant.
- [x] Detect whether `uv` is available.
- [x] Install or bootstrap `uv` only when needed.
- [x] Install TabDat as an isolated tool.
- [x] Avoid modifying unrelated environments.
- [x] Avoid requiring repository cloning.
- [x] Avoid `sudo` unless unavoidable and explicitly communicated.
- [x] Ensure the executable location is discoverable.
- [x] Print exact next steps.
- [x] Return non-zero on failure.

## 10.2 Safety and Reproducibility

- [x] Host installer source in a stable location.
- [x] Keep installer short and auditable.
- [x] Support pinned-version installation.
- [x] Verify downloads where applicable.
- [x] Test idempotent reinstallation.
- [x] Test upgrade behavior.
- [x] Test uninstall instructions.
- [x] Avoid silently editing shell profiles beyond documented requirements.
- [x] Add CI tests for supported shells/platforms where feasible.

## 10.3 User Documentation

- [ ] Document what the installer changes.
- [ ] Document install location.
- [ ] Document PATH behavior.
- [ ] Document upgrade.
- [ ] Document uninstall.
- [ ] Document offline/manual alternative.

## Exit Gate

Phase 27 is complete when:

- [ ] A fresh supported machine can execute the documented curl installer and then run `tabdat`.
- [ ] The user can immediately run TabDat from an unrelated research directory.
- [ ] Re-running the installer is safe.
- [ ] Version pinning is supported.
- [ ] Installation behavior is documented and testable.

---

# 11. Phase 28 — Homebrew Distribution

## Goal

Provide a conventional macOS/Linux package-manager installation path.

Initial target:

```bash
brew install SaehwanPark/tabdat/tabdat
```

Later, if mature enough:

```bash
brew install tabdat
```

## 11.1 Custom Tap

- [x] Create a dedicated Homebrew tap.
- [x] Add formula for the stable release.
- [x] Verify installation on Apple Silicon macOS.
- [x] Verify installation on Intel macOS if supported.
- [x] Verify Linuxbrew if supported.
- [x] Verify `brew upgrade`.
- [x] Verify `brew uninstall`.
- [x] Run canonical workflow after Homebrew installation.
- [x] Document tap usage.

## 11.2 Formula Strategy

Initially:

- [x] Decide whether the formula installs the Python package or a prebuilt release artifact.
- [x] Record decision in an ADR.
- [x] Keep formula behavior aligned with normal release versions.
- [x] Automate checksum/version updates where practical.

Later:

- [ ] Re-evaluate eligibility for `homebrew-core`.
- [ ] Submit upstream only after release cadence and external usage justify maintenance burden.

## Exit Gate

Phase 28 is complete when:

- [x] Homebrew installation works from a clean machine.
- [x] The installed `tabdat` passes canonical E2E validation.
- [x] Upgrade/uninstall behavior is verified.
- [x] Formula updates are integrated with the release process.

---

# 12. Phase 29 — Standalone Application Packaging Evaluation

## Goal

Evaluate whether TabDat should ship native-style standalone application bundles that do not require a separately managed Python installation.

Do not choose a freezer/compiler based on intuition. Benchmark alternatives.

## 12.1 Candidate Builds

Evaluate at minimum:

- [x] PyInstaller `onedir`
- [x] PyInstaller `onefile`
- [x] Nuitka standalone
- [x] Nuitka onefile if standalone succeeds

Optional additional candidates may be evaluated only if they offer a concrete advantage.

## 12.2 Evaluation Matrix

For every candidate/platform, record:

- [x] artifact size;
- [x] compressed download size;
- [x] build duration;
- [x] cold startup time;
- [x] warm startup time;
- [x] first interactive prompt latency;
- [x] canonical workflow runtime;
- [x] compatibility with DuckDB;
- [x] compatibility with Arrow/Parquet;
- [x] compatibility with plotting;
- [x] compatibility with packaged help;
- [x] optional-capability behavior;
- [x] code-signing/notarization implications;
- [x] antivirus/false-positive behavior where relevant;
- [x] operational complexity.

## 12.3 Preferred Initial Frozen Layout

Prefer evaluating directory-style packaging before one-file packaging:

```text
tabdat/
  tabdat
  _internal/
    ...
```

- [x] Verify application can live under a versioned installation directory.
- [x] Verify a stable shim/symlink can expose `tabdat` on PATH.
- [x] Measure startup against one-file extraction behavior.
- [x] Prefer the simplest option that meets startup and portability requirements.

## 12.4 Capability Scope

The first standalone application should prioritize the core product.

- [x] Do not bundle R into the standard standalone application.
- [x] Do not bundle every optional capability by default.
- [x] Determine whether conventional statistics belong in the standard binary.
- [x] Keep Bayesian/ML/spatial capability inclusion measurement-driven.
- [x] Ensure missing optional capabilities produce actionable diagnostics.

## Exit Gate

Phase 29 is complete when:

- [x] A written benchmark compares the supported packaging candidates.
- [x] The preferred standalone strategy is recorded in an ADR.
- [x] The chosen approach passes canonical E2E validation.
- [x] Artifact size/startup trade-offs are considered acceptable against recorded thresholds.
- [x] The standard build does not accidentally become a bundled R/ML/Bayesian super-environment.

---

# 13. Phase 30 — Cross-Platform Standalone Releases

## Goal

Publish prebuilt release artifacts that make TabDat feel like an independent native CLI application.

Potential release matrix:

```text
tabdat-X.Y.Z-macos-arm64.tar.gz
tabdat-X.Y.Z-macos-x86_64.tar.gz
tabdat-X.Y.Z-linux-x86_64.tar.gz
tabdat-X.Y.Z-linux-aarch64.tar.gz
tabdat-X.Y.Z-windows-x86_64.zip
```

Actual support must match tested platforms.

## 13.1 Build Matrix

- [ ] Build macOS ARM64 artifact.
- [ ] Build macOS x86_64 artifact if supported.
- [ ] Build Linux x86_64 artifact.
- [ ] Build Linux ARM64 artifact if supported.
- [ ] Build Windows x86_64 artifact if supported.
- [ ] Avoid advertising platforms without repeatable CI validation.

## 13.2 Artifact Validation

For each release artifact:

- [ ] install/extract on clean runner;
- [ ] run `tabdat --version`;
- [ ] run help lookup;
- [ ] run canonical workflow;
- [ ] run JSON-mode smoke test;
- [ ] create and inspect plot artifact;
- [ ] verify save/export behavior;
- [ ] verify paths containing spaces;
- [ ] verify operation outside repository checkout.

## 13.3 Security and Distribution

- [ ] Generate SHA-256 checksums.
- [ ] Sign artifacts where supported.
- [ ] Notarize macOS builds if required for smooth installation.
- [ ] Document provenance.
- [ ] Define vulnerability/update response process.
- [ ] Ensure installer verifies release artifact integrity.

## Exit Gate

Phase 30 is complete when:

- [ ] Supported platforms have repeatably built and tested standalone artifacts.
- [ ] Canonical workflow passes from every published artifact.
- [ ] Release assets include integrity metadata.
- [ ] Users do not need a separate Python installation for the standalone path.

---

# 14. Phase 31 — Unify Distribution Channels

## Goal

Make all installation channels converge on the same release and behavioral contract.

Supported channels may include:

```text
PyPI / uv tool
curl installer
Homebrew
standalone release download
```

## 14.1 Consistency

- [ ] All channels install the same TabDat version for a given release.
- [ ] `tabdat --version` reports consistent metadata.
- [ ] Help resources are identical.
- [ ] Canonical command behavior is identical.
- [ ] JSON schema version is identical.
- [ ] Capability differences are explicit and inspectable.

## 14.2 Installer Evolution

Once standalone artifacts are mature:

- [ ] Evaluate switching `install.sh` from `uv tool` installation to prebuilt binary installation.
- [ ] Record the decision in an ADR.
- [ ] Detect OS/architecture in installer.
- [ ] Download matching release artifact.
- [ ] Verify checksum/signature.
- [ ] Install into a versioned directory.
- [ ] Maintain stable `tabdat` shim/symlink.
- [ ] Preserve version-pinning support.

## 14.3 Homebrew Evolution

- [ ] Evaluate whether Homebrew should consume the same prebuilt artifacts.
- [ ] Avoid unnecessary rebuild of large Python dependency graphs when release binaries are authoritative.
- [ ] Keep upgrade behavior consistent with other channels.

## Exit Gate

Phase 31 is complete when:

- [ ] Installation channel choice does not change core user-visible behavior.
- [ ] Capability differences are transparent.
- [ ] Release and upgrade semantics are consistent.
- [ ] The project has one documented release source of truth.

---

# 15. Phase 32 — External Public Preview and Product Validation

## Goal

Validate the product with people who did not build it and do not know its internal assumptions.

## 15.1 Recruit External Users

Target several different user types:

- [ ] Stata-oriented analyst/statistician.
- [ ] Python-oriented data scientist.
- [ ] R-oriented quantitative researcher.
- [ ] CLI-oriented engineer or data analyst.
- [ ] At least one user working with genuinely large Parquet data.

## 15.2 Structured Dogfooding Tasks

Ask users to complete realistic workflows:

- [ ] install TabDat without developer help;
- [ ] launch it from their own project directory;
- [ ] inspect an unfamiliar dataset;
- [ ] subset/filter;
- [ ] derive a variable;
- [ ] summarize by group;
- [ ] create a plot;
- [ ] save/export results;
- [ ] write and rerun a `.td` script;
- [ ] use `help`;
- [ ] recover from at least one intentional error;
- [ ] use JSON or machine discovery if relevant to their workflow.

## 15.3 Measurable Feedback

Record:

- [ ] installation completion rate;
- [ ] time to first successful command;
- [ ] commands users try before consulting docs;
- [ ] commands users expect but cannot find;
- [ ] confusing syntax;
- [ ] confusing error messages;
- [ ] unexpected materialization/performance behavior;
- [ ] most frequently used commands;
- [ ] least-used major features;
- [ ] requests for new estimators;
- [ ] requests for better EDA/data-management features;
- [ ] willingness to reuse TabDat for another project.

## 15.4 Feedback Triage

Every substantive feedback item should be labeled:

- [ ] correctness;
- [ ] semantics;
- [ ] UX;
- [ ] performance;
- [ ] packaging;
- [ ] documentation;
- [ ] capability gap;
- [ ] new feature;
- [ ] not planned.

For each P0/P1 issue:

- [ ] assign owner;
- [ ] define reproducible acceptance test;
- [ ] resolve before stable public release or explicitly document deferral.

## Exit Gate

Phase 32 is complete when:

- [ ] At least one external-user feedback round has been completed.
- [ ] Installation has been exercised by users without repository knowledge.
- [ ] P0/P1 findings are resolved or explicitly accepted.
- [ ] Product priorities have been updated from observed usage rather than only developer intuition.

---

# 16. Phase 33 — Post-Preview Product Decision Gate

## Goal

Decide what TabDat should expand into only after stabilization, deployment, trust validation, and external usage data exist.

Do not automatically resume the old estimator roadmap.

## 16.1 Review Evidence

Before approving major new capability work:

- [ ] Review command usage from dogfooding.
- [ ] Review external feedback.
- [ ] Review install/startup measurements.
- [ ] Review dependency burden.
- [ ] Review support costs for existing estimators.
- [ ] Review reference-validation gaps.
- [ ] Review machine-interface adoption.
- [ ] Review performance bottlenecks.
- [ ] Review open architectural debt.

## 16.2 Candidate Strategic Directions

Possible directions include:

### A. Deepen Terminal EDA

Examples:

- richer table summaries;
- missingness inspection;
- data-quality diagnostics;
- better large-Parquet navigation;
- more expressive transformations;
- faster grouped exploration.

### B. Deepen Reproducibility and Automation

Examples:

- richer script constructs;
- structured execution plans;
- dry-run/explain;
- provenance/lineage;
- stronger JSON/JSONL integration;
- editor/agent integrations (Model Context Protocol / MCP server implemented; see [docs/mcp-server.md](mcp-server.md)).

### C. Deepen Conventional Statistics

Examples:

- factor-variable ergonomics;
- margins;
- model comparison;
- report/export workflows;
- a smaller number of highly trusted estimators.

### D. Expand Specialized Statistical Capabilities

Only if user evidence supports it.

### E. Expand Data Access

Only if actual workflows show demand.

## 16.3 Approval Criteria for New Major Surface

A proposed new major capability should not enter implementation until:

- [ ] a user problem is documented;
- [ ] expected users are identified;
- [ ] existing alternatives/escape hatches are insufficient;
- [ ] command-language implications are understood;
- [ ] dependency impact is measured;
- [ ] maintenance/test/reference burden is estimated;
- [ ] public semantics are specified;
- [ ] acceptance criteria are defined;
- [ ] roadmap priority is explicitly updated.

## Exit Gate

Phase 33 ends with:

- [ ] a documented post-preview product strategy;
- [ ] a prioritized next roadmap;
- [ ] explicit decisions about estimator expansion;
- [ ] explicit decisions about data-source expansion;
- [ ] explicit decisions about scripting/automation expansion;
- [ ] obsolete roadmap items archived or superseded.

---

# 17. `tabdat doctor` Capability and Environment Diagnostics

This can be implemented when capability modularization and deployment work make it useful.

Target:

```text
$ tabdat doctor

TabDat X.Y.Z

Core
  DuckDB        ✓
  Parquet       ✓
  Arrow         ✓
  Plotting      ✓

Statistics
  statsmodels   ✓
  linearmodels  ✓

Optional
  ML            ✓
  Bayesian      -
  Spatial       -
  R             -
```

Checklist:

- [x] Define machine-readable capability registry.
- [x] Surface installed capabilities.
- [x] Surface relevant backend/library versions.
- [x] Detect R runtime availability.
- [x] Detect required R packages where relevant.
- [x] Detect broken optional installations.
- [x] Provide actionable install/repair commands.
- [x] Support JSON output.
- [x] Include release/build metadata useful for bug reports.

This command should become a standard first step in deployment support.

---

# 18. Performance and Distribution Scorecard

Maintain a tracked scorecard rather than discussing "lightweight" qualitatively.

For every release candidate, measure where practical:

## Core CLI

- [ ] executable/package size;
- [ ] compressed download size;
- [ ] dependency count;
- [ ] cold startup time;
- [ ] warm startup time;
- [ ] time to interactive prompt;
- [ ] peak memory at startup.

## Canonical Workflow

- [ ] eager workflow runtime;
- [ ] lazy workflow runtime;
- [ ] materialization count;
- [ ] materialization reasons;
- [ ] peak memory;
- [ ] deterministic replay equality.

## Installation

- [x] PyPI/uv install success;
- [x] curl install success;
- [x] Homebrew install success;
- [ ] standalone install/extract success;
- [x] upgrade success;
- [x] uninstall success.

## Portability

- [x] macOS ARM64;
- [ ] macOS x86_64 if supported;
- [x] Linux x86_64;
- [ ] Linux ARM64 if supported;
- [ ] Windows x86_64 if supported.

Do not invent fixed performance thresholds prematurely.

Instead:

- [x] establish baseline measurements;
- [x] define acceptable thresholds in an ADR;
- [ ] fail release checks when agreed thresholds regress materially without explicit approval.

---

# 19. Release Readiness Checklist

A stable public release should not be declared until all applicable items are checked.

## Product

- [x] Canonical EDA workflow is documented.
- [x] Core semantics are stable.
- [x] Error behavior is predictable.
- [x] Machine output schema is versioned/stable.
- [x] Major execution state is inspectable.

## Trust

- [x] Tier 1 estimators have reference validation.
- [x] Every estimator has an explicit validation status.
- [x] Known statistical differences are documented.

## Architecture

- [x] Core does not import specialized stacks.
- [x] Optional capabilities fail cleanly.
- [x] Command registration is internally consistent.
- [x] Architecture docs reflect reality.

## Packaging

- [x] Clean wheel install passes.
- [x] Global `tabdat` invocation passes.
- [x] Package naming/versioning is finalized.
- [x] Supported Python versions are documented.

## Distribution

- [x] At least one low-friction installation path exists.
- [x] Upgrade path exists.
- [x] Uninstall path exists.
- [x] Release artifacts have checksums/provenance.

## QA

- [x] Unit tests pass.
- [x] Static analysis passes.
- [x] Formatting/lint passes.
- [x] Integrated E2E passes.
- [x] Canonical replay passes.
- [x] Clean-install E2E passes.
- [x] Supported-platform release tests pass.

## External Validation

- [ ] External users have installed the tool.
- [ ] External users have completed realistic workflows.
- [ ] P0/P1 feedback is resolved or explicitly accepted.

---

# 20. Recurring Roadmap Review Checklist

Review this document regularly rather than treating checked items as historical decoration.

Recommended review cadence:

- after every meaningful release;
- after every major architecture ADR;
- after every deployment milestone;
- after every external feedback round;
- before approving a new major feature family.

At each review:

- [ ] Check newly completed items.
- [ ] Add links to the validating PR/commit/report where useful.
- [ ] Remove or rewrite obsolete criteria.
- [ ] Confirm phase sequencing still reflects current risks.
- [ ] Confirm no completed implementation contradicts an unchecked prerequisite.
- [ ] Reassess whether breadth expansion remains blocked.
- [ ] Reassess package/dependency boundaries.
- [ ] Reassess supported platforms.
- [ ] Reassess performance thresholds.
- [ ] Reassess statistical validation status.
- [ ] Reassess external-user priorities.
- [ ] Update `Last Reviewed` metadata or roadmap history if maintained.

---

# 21. Immediate Next Actions

These should be treated as the current working queue.

## Priority 0 — Scope and Roadmap Alignment

- [ ] Add this roadmap to the repository.
- [ ] Link it from `README.md`, `CONTRIBUTING.md`, or another developer entry point.
- [ ] Mark `docs/dev_phase.md` as historical/secondary for forward planning.
- [ ] Confirm no active issue/PR assumes estimator expansion has priority over stabilization.
- [ ] Create or update tracking issues for the remaining Phase 24 work.

## Priority 1 — Finish Semantic Stabilization

- [ ] Audit which Phase 24 semantic items are already complete.
- [ ] Check completed items in this roadmap.
- [ ] Create focused issues for remaining semantics.
- [ ] Close P0/P1 ambiguity before packaging work changes public expectations.

## Priority 2 — Modularize Capability Boundaries

- [ ] Measure startup import graph.
- [ ] Identify specialized imports triggered by core CLI startup.
- [ ] Draft capability-layer ADR.
- [ ] Begin extracting executor handlers by command family.
- [ ] Add clean-core tests without Bayesian/spatial/ML/R dependencies.

## Priority 3 — Establish Statistical Trust Matrix

- [ ] Create machine-readable validation matrix.
- [ ] Add `regress` reference validation first.
- [ ] Add `logit`/`probit`/`poisson` reference validation.
- [ ] Publish validation status in docs.

## Priority 4 — Prepare Global Installation

- [ ] Finalize package naming.
- [ ] Build wheel.
- [ ] Test clean wheel installation.
- [ ] Test global installation from Git URL with `uv tool`.
- [ ] Publish pre-release to PyPI.
- [ ] Verify `uv tool install <final-package>`.

## Priority 5 — Add CI and Release Automation

- [ ] Add PR validation workflow.
- [ ] Add clean-wheel workflow.
- [ ] Add tagged release workflow.
- [ ] Require canonical E2E before publication.

## Priority 6 — Add Frictionless Install Channels

- [ ] Implement `install.sh`.
- [ ] Add custom Homebrew tap.
- [ ] Test clean-machine install/upgrade/uninstall.

## Priority 7 — Evaluate Standalone Builds

- [ ] Benchmark PyInstaller.
- [ ] Benchmark Nuitka.
- [ ] Record artifact-size/startup results.
- [ ] Select strategy via ADR.
- [ ] Publish experimental standalone release artifacts.

---

# 22. Final Direction

TabDat should now optimize for depth of trust and ease of use rather than breadth of command count.

The development question for every major proposal should be:

> Does this make the existing TabDat product more trustworthy, installable, understandable, reproducible, portable, or useful in real research workflows?

Until the public-preview gates are passed, a new estimator is usually lower priority than:

- making `tabdat` install globally;
- making core startup lightweight;
- making semantics explicit;
- making statistical results reference validated;
- making execution inspectable;
- making release artifacts reproducible;
- making the canonical workflow work identically outside the source repository;
- observing what external users actually need.

The desired end state is a tool that feels like an independent application:

```bash
$ tabdat
```

while retaining the strengths of its Python/DuckDB ecosystem internally and exposing specialized capabilities only when users actually need them.

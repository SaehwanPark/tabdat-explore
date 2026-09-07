# Request Summary: `assert` quality gate

- **Objective:** Continue product catch-up with one bounded, user-facing data-quality slice that helps analysts coming from Stata, SAS, and SPSS without turning TabDat-Explore into a compatibility clone.
- **Selected slice:** Add a read-only `assert <boolean-expression>` command for active-row quality gates.
- **Why this slice:** It complements the delivered `missing` profiler with a deterministic validation primitive for scripted terminal EDA and data-quality checks, while avoiding estimator-family expansion.
- **Roadmap fit:** Phase 24A / Deepen Terminal EDA and data-quality diagnostics; no new estimator family, connector, GUI, or broad compatibility surface.
- **Touched surfaces:** command model/parser, DuckDB and Polars-lazy predicate aggregation, executor result/error handling, formatter, CLI effect/schema, shell completion, help/reference/user semantics/docs, focused parser/backend/executor/CLI/JSON/lazy tests, implementation and QA reports.
- **Non-goals:** row filtering, generated flags, row-level diagnostics, loops/control flow, assignment, options, `if`, by-groups, custom missing-value rules, or native Stata/SAS/SPSS compatibility.
- **Constraints:** predicates reuse TabDat's existing expression and missing semantics; true rows pass, false or missing predicate rows fail; empty datasets pass; failure reports deterministic failed/checked counts and leaves the active dataset/session relation unchanged; aggregate scans preserve Polars-lazy mode; maintain 2-space style and `uv` validation workflow.

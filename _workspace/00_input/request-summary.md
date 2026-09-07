# Request Summary

- **Objective:** Continue the product catch-up work with one bounded, user-facing terminal-EDA slice that helps analysts coming from Stata, SAS, and SPSS without turning TabDat-Explore into a compatibility clone.
- **Selected slice:** Add a `missing [varlist]` command for compact missingness inspection.
- **Why this slice:** `codebook` exposes per-column missing counts alongside other profile details, but analysts need a fast, scan-friendly overview of missing counts, nonmissing counts, and percentages before filtering, modeling, or exporting data. This is a natural Stata `misstable summarize` / SAS/SPSS frequency-workflow analogue while remaining a TabDat-native command.
- **Roadmap fit:** Phase 24A language/EDA stabilization and the Deepen Terminal EDA direction; no new estimator family, connector, GUI, or broad compatibility surface.
- **Touched surfaces:** command model/result, parser, DuckDB and Polars-lazy backend profiling, executor dispatch/materialization policy, formatter, CLI schema/effects, shell completion, help/reference docs, focused parser/backend/executor/CLI tests, implementation and QA reports.
- **Non-goals:** missing-value pattern matrices, user-defined missing-value codes, imputation, row filtering, changing existing `codebook` or estimation missingness semantics, or native Stata/SAS/SPSS compatibility.
- **Constraints:** use explicit null-based missingness already defined by TabDat; preserve variable order; return deterministic human and JSON results; validate unknown variables before scanning; keep Polars-lazy mode lazy while allowing a bounded aggregate scan; maintain the 2-space style and `uv` validation workflow.

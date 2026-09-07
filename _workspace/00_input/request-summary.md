# Request Summary

- **Objective:** Continue product catch-up with one bounded, user-facing data-management slice that helps analysts coming from Stata, SAS, and SPSS without turning TabDat-Explore into a compatibility clone.
- **Selected slice:** Add a stable ascending `sort <varlist>` command for active-row ordering.
- **Why this slice:** TabDat already defines row-order guarantees for previews and relation operations, but users lack a direct terminal command to arrange the active dataset before inspection, export, or downstream analysis. Stable sorting is a daily Stata `sort`, SAS `PROC SORT`, and SPSS `SORT CASES` workflow.
- **Roadmap fit:** Phase 24A active-row ordering and Deepen Terminal EDA/data-management; no new estimator family, connector, GUI, or broad compatibility surface.
- **Touched surfaces:** command model/parser, DuckDB and Polars-lazy backend row ordering, executor state/metadata preservation, CLI effect/schema, shell completion, help/reference/user semantics/docs, focused parser/backend/executor/CLI/lazy tests, implementation and QA reports.
- **Non-goals:** descending sort/`gsort`, arbitrary expressions, multiple sort modes, deduplication, grouping, or native Stata/SAS/SPSS file compatibility.
- **Constraints:** ascending native scalar order with nulls last; stable original-order ties; preserve all columns, labels, panel metadata, and requested sort-column order; keep Polars-lazy mode lazy; reject unknown columns before state changes; maintain 2-space style and `uv` validation workflow.

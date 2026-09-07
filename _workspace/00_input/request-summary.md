# Request summary

The active goal is to improve TabDat with useful, modernized capabilities inspired by current Stata, SAS, and SPSS workflows without sacrificing TabDat's Parquet-first, terminal-native, reproducible, typed, and explicit-semantics design.

## Completed prior slice

The previous bounded slice delivered a read-only `assert <boolean-expression>` quality gate for active-row validation, with deterministic false/missing counts, eager/DuckDB-lazy/Polars-lazy aggregate support, and no state mutation.

## Current bounded slice

Add a read-only `duplicates` data-quality report. Duplicate detection is a common Stata `duplicates report`, SAS `PROC SORT`/`NODUPKEY`, and SPSS duplicate-case workflow, and complements the existing `missing` and `assert` quality commands without adding an estimator family or broad compatibility surface.

## Phase fit

This is a bounded Phase 24 product-center stabilization/data-quality slice. It defines deterministic null-aware grouping, preserves eager/DuckDB-lazy/Polars-lazy behavior, and does not add mutation, random sampling, or backend-specific dependencies.

## Touched surfaces

- parser/model command contract;
- DuckDB and Polars-lazy aggregate backend;
- executor dispatch and lazy-materialization allowlist;
- human/JSON result formatting, command effects, schema discovery, and shell completion;
- in-app help, command references, language semantics, MCP workflow guidance, spec/changelog records;
- focused parser/backend/executor/CLI tests.

## Non-goals

Do not implement `duplicates list`, `duplicates drop`, `duplicates tag`, fuzzy matching, approximate matching, row-level duplicate output, or a new estimator/data-source family in this slice.

# Request summary

The active goal is to improve TabDat with useful, modernized capabilities inspired by current Stata, SAS, and SPSS workflows without sacrificing TabDat's Parquet-first, terminal-native, reproducible, typed, and explicit-semantics design.

## Completed prior slices

- `assert <boolean-expression>` quality gates with deterministic false/missing counts and eager/DuckDB-lazy/Polars-lazy aggregate support.
- `duplicates [report] [varlist]` data-quality reports with null-aware grouping and eager/DuckDB-lazy/Polars-lazy aggregate support.
- `datasignature` reproducibility fingerprints with canonical cross-engine SHA-256 scans and Polars-lazy plan preservation.

## Current bounded slice

Add `gsort [+|-]varlist` for stable per-key ascending/descending ordering. Directional sorting is a
compact Stata `gsort` feature also familiar from SAS descending sort keys and SPSS sort-case
workflows, and it extends the existing native, nulls-last, deterministic `sort` contract without
adding an estimator family or broad compatibility surface.

## Phase fit

This is a bounded Phase 24 product-center stabilization/ordering slice. It defines explicit per-key
ascending/descending semantics, stable ties, and nulls-last behavior; preserves eager/DuckDB-lazy/
Polars-lazy behavior; and does not add random sampling, estimator families, or backend-specific
dependencies.

## Touched surfaces

- parser/model command contract and direction-key validation;
- DuckDB and Polars-lazy stable sorting backend;
- executor dispatch and lazy-materialization allowlist;
- human/JSON transform output, command effects, schema discovery, and shell/column completion;
- in-app help, command references, language semantics, MCP guidance, user-guide/spec/changelog
  records;
- focused parser/backend/executor/CLI tests.

## Non-goals

Do not change existing ascending `sort` syntax, add descending expressions to unrelated commands,
implement random ordering, add row filters/options, support `by: gsort`, introduce a new estimator or
data-source family, or claim Stata/SAS/SPSS syntax compatibility.

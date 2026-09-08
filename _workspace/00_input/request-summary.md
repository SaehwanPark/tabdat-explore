# Request summary

The active goal is to improve TabDat with useful, modernized capabilities inspired by current Stata, SAS, and SPSS workflows without sacrificing TabDat's Parquet-first, terminal-native, reproducible, typed, and explicit-semantics design.

## Completed prior slices

- `assert <boolean-expression>` quality gates with deterministic false/missing counts and eager/DuckDB-lazy/Polars-lazy aggregate support.
- `duplicates [report] [varlist]` data-quality reports with null-aware grouping and eager/DuckDB-lazy/Polars-lazy aggregate support.
- `datasignature` reproducibility fingerprints with canonical cross-engine SHA-256 scans and Polars-lazy plan preservation.
- `gsort [+|-]varlist` stable mixed-direction ordering with nulls-last behavior and eager/DuckDB-lazy/Polars-lazy support.

## Current bounded slice

Add `isid varlist [, missok]` as a read-only key-uniqueness quality gate. It is a compact Stata
`isid` feature with parallels to SAS key checks and SPSS duplicate-ID validation, and it complements
`duplicates` by turning key integrity into a deterministic, scriptable assertion without mutating the
active dataset or adding an estimator family.

## Phase fit

This is a bounded Phase 24 product-center stabilization/data-quality slice. It defines explicit
composite-key uniqueness and missing-key semantics, preserves eager/DuckDB-lazy/Polars-lazy behavior,
and avoids broad validation frameworks, row-level tagging, mutation, or backend-specific dependencies.

## Touched surfaces

- parser/model command contract and `missok` flag validation;
- DuckDB and Polars-lazy aggregate key validation;
- executor dispatch, typed result/error behavior, and lazy-materialization allowlist;
- human/JSON output, command effects, schema discovery, and shell/column completion;
- in-app help, command references, language semantics, MCP guidance, user-guide/spec/changelog
  records;
- focused parser/backend/executor/CLI tests.

## Non-goals

Do not add row filters, duplicate listing/tagging/dropping, automatic repair, `by: isid`, arbitrary
validation rules, a stored key registry, a broad SPSS/SAS validation framework, a new estimator or
data-source family, or a syntax-compatibility claim for Stata/SAS/SPSS.

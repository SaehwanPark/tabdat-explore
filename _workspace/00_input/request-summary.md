# Request summary

The active goal is to improve TabDat with useful, modernized capabilities inspired by current Stata, SAS, and SPSS workflows without sacrificing TabDat's Parquet-first, terminal-native, reproducible, typed, and explicit-semantics design.

## Completed prior slices

- `assert <boolean-expression>` quality gates with deterministic false/missing counts and eager/DuckDB-lazy/Polars-lazy aggregate support.
- `duplicates [report] [varlist]` data-quality reports with null-aware grouping and eager/DuckDB-lazy/Polars-lazy aggregate support.

## Current bounded slice

Add a read-only `datasignature` reproducibility fingerprint. Data signatures are a compact Stata
`datasignature`-inspired integrity primitive that complements SAS comparison and SPSS validation
workflows without adding an estimator family, metadata store, or broad compatibility surface.

## Phase fit

This is a bounded Phase 24 product-center stabilization/reproducibility slice. It defines a
versioned canonical hash over schema, ordered values, and explicit missing/non-finite encodings;
preserves eager/DuckDB-lazy/Polars-lazy behavior; and does not add mutation, random sampling, or
backend-specific dependencies.

## Touched surfaces

- parser/model command contract;
- bounded DuckDB/Arrow and Polars-lazy row-scan backend;
- executor dispatch and lazy-materialization allowlist;
- human/JSON result formatting, command effects, schema discovery, and shell completion;
- in-app help, command references, language semantics, MCP workflow guidance, user-guide,
  spec/changelog records;
- focused parser/backend/executor/CLI tests.

## Non-goals

Do not implement stored baselines, `datasignature verify`/`reset`, filtered or varlist signatures,
algorithm options, byte-level Parquet checksums, metadata-label hashing, row-level diffs, a new
estimator/data-source family, or a compatibility clone of Stata/SAS/SPSS behavior.

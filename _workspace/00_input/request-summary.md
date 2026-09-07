# Request Summary: Variable and Value Labels (Slice 1)

## 1. Goal
Add Stata/SPSS-inspired session-local variable labels and value-label dictionaries so analysts can document and inspect categorical/numeric codes without leaving TabDat. Stay Stata-inspired (not compatible), deepen terminal EDA, and do not add estimator families.

## 2. Why this slice
- Expected end users from Stata/SPSS rely on data-dictionary metadata for `describe`/`codebook`/review workflows.
- Fits roadmap direction “Deepen Terminal EDA” and product philosophy (predictable modern behavior, small reliable surface).
- Explicitly not broad Stata compatibility and not a new estimator family (allowed under the forward-roadmap breadth freeze as bounded data-management UX).

## 3. Constraints & Assumptions
- Session-local metadata on the active dataset (like panel metadata); not persisted into Parquet on `save`/`export` in this slice.
- Value labels attach by set name; display in `describe` and `codebook` first; `tabulate` labeled display deferred.
- One temporary branch / one PR for this slice.

## 4. Touched Surfaces
- Parser, models, executor metadata helpers, formatter, shell completions, CLI effects/schema, help topic, command-reference, SPEC/CHANGELOG, tests, LESSONS.md when useful.

## 5. Non-goals
- Stata `label language`, multilingual labels, graph label options, SPSS `.sav` round-trip, Parquet metadata persistence, `encode`/`decode`, labeled `tabulate` cells.

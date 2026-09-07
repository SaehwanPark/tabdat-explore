# Request Summary

- **Objective:** Continue the product catch-up work with one bounded, user-facing slice that helps analysts coming from Stata, SAS, and SPSS without turning TabDat-Explore into a compatibility clone.
- **Selected slice:** Persist the session-local data dictionary with `label save` / `label use` JSON commands.
- **Why this slice:** Variable labels and value-label dictionaries are now useful for inspection, tabulation, and encode/decode, but they disappear at the end of a session. Reusable metadata is an expected analyst workflow and a natural extension of the existing label surface.
- **Roadmap fit:** Phase 24A product-center stabilization and the existing data-dictionary UX; no new estimator family, connector, or broad compatibility work.
- **Touched surfaces:** parser/model, pure label-document serialization, executor validation and file effects, CLI command schema/effect declaration, help/reference docs, focused unit/executor/CLI tests, implementation and QA reports.
- **Non-goals:** embedding labels into every output format, importing arbitrary Stata/SAS/SPSS metadata, changing existing `save`/`export` behavior, or introducing a public plugin/API contract.
- **Constraints:** preserve exact current label semantics; use deterministic versioned JSON; reject malformed/incompatible dictionaries atomically; keep Polars-lazy metadata operations from forcing materialization; maintain the 2-space style and `uv` validation workflow.

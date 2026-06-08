# Request Summary: Phase 19 Slice 8 DML

## Goal

Resume development from the latest checkpoint on `main` and implement the next bounded Phase 19
slice: partial-linear double/debiased machine learning (DML) for binary treatment-effect estimation
under high-dimensional controls.

## Checkpoint

- Branch base: `main` at latest (`a170850`)
- Working branch: `temp/phase19-slice8-dml-linear-treatment`
- Prior completed slice: Phase 19 slice 7 (`postlasso`)

## Touched Surfaces

- Parser (`dml`, `estat dml`)
- Executor (cross-fitted sklearn Lasso nuisances + final OLS stage)
- Formatter, shell completions, help, extension registry
- Tests and SDD docs (`SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `README.md`)

## Assumptions

- Partial-linear binary-treatment ATE only; no IV, CATE, or predict routing in this slice.
- Python-first via existing `scikit-learn` + `statsmodels`; no new runtime dependencies.
- Binary treatment validation follows existing `did`/`drdid` conventions.

## Non-goals

- Bayesian MCMC prefix, spatial GIS ingestion, advanced SAR diagnostics.
- `predict` after `dml`, panel preconditions, R fallback.

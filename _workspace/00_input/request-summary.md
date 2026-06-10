# Request Summary: Phase 19 Bayesian `estat bayes` Slice

## Goal

Resume from the latest checkpoint and implement the next coherent Phase 19 slice using TDD,
documentation updates, PR publication, and independent code review.

## Selected Scope

- Add `estat bayes` after successful `bayes:` MCMC fits.
- Support both `bayes: regress` and `bayes: logit`.
- Report deterministic in-terminal MCMC diagnostics from retained ArviZ posterior state.

## Phase Fit

- Roadmap phase: Phase 19 modern extensions.
- This is the smallest Bayesian follow-up after the completed posterior predictive slice.

## Non-Goals

- No trace, density, or autocorrelation plots.
- No posterior interval output columns.
- No out-of-sample Bayesian prediction syntax.
- No changes to legacy `bayes linear` execution or prediction behavior.

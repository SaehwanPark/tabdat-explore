# Request Summary: Phase 19 Bayesian Posterior Predictive Slice

## Goal

Resume from the latest checkpoint and implement the next coherent Phase 19 slice using TDD,
documentation updates, PR publication, and independent code review.

## Selected Scope

- Add `predict <newvar>, posterior_predictive` after successful `bayes:` MCMC fits.
- Support both `bayes: regress` and `bayes: logit`.
- Write row-wise posterior predictive means into the active dataset.

## Phase Fit

- Roadmap phase: Phase 19 modern extensions.
- This is the smallest Bayesian follow-up after the completed `bayes:` MCMC prefix slice.

## Non-Goals

- No trace, density, or autocorrelation diagnostic plots.
- No posterior interval columns.
- No out-of-sample prediction syntax.
- No changes to legacy `bayes linear` prediction behavior.

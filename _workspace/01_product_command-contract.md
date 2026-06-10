# Phase 19 Command Contract: Bayesian `estat bayes` Diagnostics

## Roadmap Phase

- Phase 19 modern extensions.
- Bayesian diagnostics follow-up after the completed `bayes:` MCMC prefix and posterior predictive
  slices.

## Syntax

```stata
bayes [, options]: regress <y> <xvars>
estat bayes

bayes [, options]: logit <y> <xvars>
estat bayes
```

## Behavior

- `bayes` is a model-specific `estat` subcommand.
- The option is available only after a successful `bayes:` prefix fit.
- The executor reads retained ArviZ posterior state from the latest `bayes:` model.
- Output is a deterministic table with parameter-level metrics:
  `ess_bulk`, `ess_tail`, `r_hat`, `mcse_mean`, and `mcse_sd`.
- Output also includes sampler-level `divergence_count`.
- `bayes: regress` includes `sigma` rows; `bayes: logit` does not.
- Unavailable diagnostics from short-chain runs render as `not_available`.

## Guards

- `estat bayes` without a prior `bayes:` fit raises `ExecutionError`.
- `estat bayes` after legacy `bayes linear` raises `ExecutionError`.
- Existing `estat` subcommands remain unchanged.
- Existing `bayes:` prediction behavior remains unchanged.

## Acceptance Criteria

- Parser accepts `estat bayes`.
- Shell completion exposes `bayes` under `estat`.
- Executor returns deterministic diagnostics tables after both `bayes: regress` and
  `bayes: logit`.
- CLI smoke coverage exercises `bayes: regress` followed by `estat bayes`.
- Focused tests, `basedpyright`, and `ruff` checks pass.

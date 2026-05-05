---
title: "Reorganized Microeconometric Topics"
author: "Sae-Hwan Park"
date: 2026-05-05
---

Based on what the book "Microeconometrics using Stata" covers, below is a **topologically sorted reorganization** where:

* earlier items = **prerequisites, reusable primitives, or broadly independent**
* later items = **dependent, composite, or specialized capabilities**
* each layer builds cleanly on previous ones

---

# 🧠 Topologically Sorted Capability Graph (Microeconometrics System)

## **Layer 0 — Core Infrastructure (must exist first)**

These are non-negotiable primitives everything else depends on.

### Data & Execution Engine

* Data frame abstraction (columns, labels, missing values)
* Type system (numeric, categorical, panel indexing)
* Vectorized operations
* Group-by / aggregation
* Merge / reshape (wide ↔ long)

### Reproducibility & Workflow

* Script execution (do-files equivalent)
* Logging + output capture
* Random number seeding

### Programming Primitives

* Macros / variables
* Control flow (loops, conditionals)
* Functions / modular code

---

## **Layer 1 — Mathematical & Statistical Primitives**

These enable *any* estimator.

### Linear Algebra Core

* Matrix operations (multiply, invert, decompose)
* Sparse support (optional but valuable)

### Probability & Statistics

* Distributions (normal, binomial, Poisson, etc.)
* Sampling and random number generation
* Moments (mean, variance, covariance)

### Optimization Engine

* Objective function abstraction
* Gradient / Hessian support
* Solvers (Newton, quasi-Newton, BFGS)

---

## **Layer 2 — Simulation & Resampling**

Independent of specific models, widely reused.

* Monte Carlo simulation framework
* Bootstrap (nonparametric, parametric)
* Resampling utilities
* Performance evaluation tools

---

## **Layer 3 — Baseline Estimation Frameworks**

These define the *general estimation paradigms*.

### Least Squares Framework

* Ordinary Least Squares (OLS)
* Weighted least squares
* Residual computation + diagnostics hooks

### Maximum Likelihood Framework

* Log-likelihood specification
* Generic MLE solver interface
* Score and information matrix

### Method of Moments / GMM

* Moment condition abstraction
* Weighting matrix estimation
* Two-step GMM

---

## **Layer 4 — Core Linear Models**

Built directly on Layer 3.

### Linear Regression

* OLS estimation + inference
* Prediction and fitted values

### Robust Inference

* Heteroskedasticity-robust SEs
* Cluster-robust SEs

### Generalized Least Squares

* Feasible GLS
* Variance structure modeling

### Diagnostics

* Residual analysis
* Specification tests
* Multicollinearity detection

---

## **Layer 5 — Endogeneity & Identification Tools**

Depend on linear model + inference infrastructure.

### Instrumental Variables

* Two-stage least squares (2SLS)
* Weak instrument diagnostics
* Overidentification tests

### Control Function Methods

* Residual inclusion approaches
* Endogeneity correction workflows

---

## **Layer 6 — Panel Data Foundations**

Requires linear models + IV + data structure support.

### Panel Data Handling

* Indexing (entity, time)
* Within/between transformations

### Panel Estimators

* Fixed effects (FE)
* Random effects (RE)
* Hausman test

---

## **Layer 7 — Nonlinear Estimation Core**

Requires MLE + optimization.

### Binary Choice Models

* Logit / probit estimation
* Marginal effects

### General Nonlinear Models

* Nonlinear regression
* Prediction and interpretation tools

---

## **Layer 8 — Limited Dependent Variable Models**

Built on nonlinear estimation.

* Tobit (censoring)
* Truncated regression
* Sample selection (Heckman)

---

## **Layer 9 — Discrete Choice Systems**

Depend on nonlinear + likelihood framework.

* Multinomial logit
* Conditional logit
* Nested logit
* IIA diagnostics

---

## **Layer 10 — Count Data Models**

Parallel branch from nonlinear MLE.

* Poisson regression
* Negative binomial
* Overdispersion handling

---

## **Layer 11 — Mixture & Zero-Inflated Models**

Depend on count + latent structure + MLE.

* Zero-inflated models
* Hurdle models
* Finite mixture models
* EM algorithm

---

## **Layer 12 — Duration / Survival Models**

Require likelihood + specialized distributions.

* Hazard and survival functions
* Parametric survival models
* Cox proportional hazards

---

## **Layer 13 — Dynamic & Advanced Panel Models**

Depend on panel + GMM + nonlinear.

* Dynamic panel (Arellano–Bond)
* GMM for panels
* Endogenous regressors in panels

---

## **Layer 14 — Nonlinear Panel Models**

Depend on nonlinear + panel structure.

* Fixed-effects logit
* Random-effects nonlinear models
* Incidental parameters problem

---

## **Layer 15 — Flexible / Distributional Methods**

More independent but require core estimation.

* Quantile regression
* Robust distributional analysis

---

## **Layer 16 — Semiparametric & Nonparametric Methods**

Require strong statistical primitives.

* Kernel regression
* Local polynomial regression
* Bandwidth selection
* Partially linear models

---

## **Layer 17 — Causal Inference Framework**

Cross-cutting but depends on many earlier tools.

### Treatment Effects

* Potential outcomes framework
* ATE / ATT estimation

### Matching & Weighting

* Propensity scores
* Matching estimators

### Endogenous Treatment

* IV treatment effects
* Selection correction

---

## **Layer 18 — Modern / Extended Capabilities**

Built last due to broad dependencies.

### Machine Learning Integration

* Lasso / Ridge
* Cross-validation
* Post-selection inference

### Bayesian Methods

* Prior/posterior computation
* MCMC (Gibbs, Metropolis-Hastings)

### Spatial Models

* Spatial lag / error models
* Spatial weight matrices

---

# 🧩 Key Design Insights

### 1. Separate **Estimation Engines from Models**

* OLS, MLE, GMM = reusable cores
* Everything else = thin wrappers

### 2. Treat **Panel, Nonlinear, and Causal** as Orthogonal Axes

* Panel ≠ nonlinear ≠ causal
* Your architecture should allow combinations:

  * nonlinear + panel
  * panel + IV
  * nonlinear + causal

### 3. Build Around **Composable Primitives**

* likelihood()
* moments()
* transform(panel)
* simulate()


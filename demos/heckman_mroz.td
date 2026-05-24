# ==============================================================================
# Heckman Sample Selection Model Demonstration (Mroz 1987)
# ==============================================================================
# This demo replicates a classic sample-selection model of married women's wages,
# adjusting for selection bias in labor force participation.
#
# Dataset: Panel Study of Income Dynamics (PSID) 1976 data.
# ==============================================================================

# 1. Load the dataset from the public Stata/Wooldridge repository
use https://www.stata.com/data/jwooldridge/eacsap/mroz.dta

# 2. Descriptive statistics of variables
summarize wage lwage educ exper age kidslt6 nwifeinc

# 3. Fit Heckman Selection Model
# Outcome Equation: log wage (lwage) explained by education and experience.
# Selection Equation: in labor force (inlf) explained by non-wife income,
# education, experience, age, and children indicators.
heckman lwage educ exper, selectdep(inlf) select(educ exper expersq age kidslt6 kidsge6 nwifeinc)

# 4. Predict expected outcome (xb) and selection residuals
predict wage_hat, xb
predict selection_resid, residuals

# 5. Display a preview of original and generated predictions
select inlf wage lwage educ exper wage_hat selection_resid
head 10

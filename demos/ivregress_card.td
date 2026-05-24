# ==============================================================================
# Instrumental Variables (IV/2SLS) returns to education (Card 1995)
# ==============================================================================
# This demo replicates David Card's return to schooling model, addressing the
# endogeneity of education using proximity to a 4-year college (nearc4)
# as an instrument.
#
# Dataset: Card (1995) returns to schooling dataset.
# ==============================================================================

# 1. Load the dataset from the public Stata/Wooldridge repository
use https://www.stata.com/data/jwooldridge/eacsap/card.dta

# 2. Summarize key indicators
summarize lwage educ exper black south smsa nearc4

# 3. Fit baseline OLS model
# Predict log wage (lwage) using education and exogenous control variables
regress lwage educ exper expersq black south smsa

# 4. Fit IV/2SLS model
# Treats education (educ) as endogenous, instrumenting it with nearc4
ivregress 2sls lwage exper expersq black south smsa, endog(educ) iv(nearc4)

# 5. Run first-stage diagnostics (instrument strength, F-statistic)
estat firststage

# 6. Run endogeneity diagnostic test (Durbin / Wu-Hausman)
estat endogenous

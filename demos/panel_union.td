# ==============================================================================
# Panel Data Regression and Hausman Specification Test
# ==============================================================================
# This demo replicates panel regressions (Fixed Effects vs. Random Effects) on
# young women's wages and union status, running the Hausman specification test
# to determine the preferred model.
#
# Dataset: NLSY Young Women Union dataset.
# ==============================================================================

# 1. Load the dataset from the public Stata-press r14 repository
use https://www.stata-press.com/data/r14/union.dta

# 2. Set panel entity and time indexing variables
panel idcode year

# 3. View structural panel characteristics
panel

# 4. Fit Fixed Effects (FE) panel model
xtreg union age grade south, fe

# 5. Fit Random Effects (RE) panel model
xtreg union age grade south, re

# 6. Run the Hausman specification test
estat hausman

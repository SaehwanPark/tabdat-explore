# ==============================================================================
# Doubly Robust Difference-in-Differences (drdid) Estimation
# ==============================================================================
# This demo performs Doubly Robust Difference-in-Differences estimation on a
# simulated balanced panel dataset, showcasing outcomes regression, inverse
# probability weighting, and augmented doubly robust estimators.
# ==============================================================================

# 1. Load the simulated parquet dataset
use demos/drdid_simulated.parquet

# 2. Set panel entity and time indexing variables
panel firm_id year

# 3. Fit the default AIPW (Augmented Inverse Probability Weighting) estimator
drdid wage exposure, treat(treated) post(post) method(aipw)

# 4. View post-estimation diagnostics (cell counts, propensity scores, overlap check)
estat drdid

# 5. Fit the IPW (Inverse Probability Weighting) estimator
drdid wage exposure, treat(treated) post(post) method(ipw)

# 6. Fit the OR (Outcome Regression) estimator
drdid wage exposure, treat(treated) post(post) method(or)

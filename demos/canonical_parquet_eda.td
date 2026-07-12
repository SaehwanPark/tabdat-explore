# Canonical Parquet-first terminal EDA workflow.
#
# The source dataset should contain age, fare, sibsp, parch, and class columns.
# The integrated harness runs this script against a converted Titanic sample.

let source = artifacts/e2e/data/titanic.parquet
let output = artifacts/e2e/s6/canonical_summary.parquet

use $source, lazy engine=duckdb
describe
count
codebook age fare class embarked survived
keep if age >= 18
generate family_size = sibsp + parch + 1
summarize age fare family_size
by class: summarize fare
collapse mean age fare family_size, by(class)
export $output, replace

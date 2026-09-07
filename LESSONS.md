# Lessons

## 2026-09-06 — Catch-up vs philosophy under the forward roadmap

**Trap:** Treating “catch up with Stata/SPSS” as license for broad command compatibility or new
estimator families conflicts with `docs/tabdat_forward_roadmap.md` (breadth freeze + deepen EDA
first).

**Resolution:** Prefer bounded data-management / terminal-EDA slices that analysts from Stata/SPSS
expect daily (e.g. variable/value labels) while keeping “inspired, not compatible” semantics.
Record the choice in the roadmap’s Deepen Terminal EDA section and keep one slice = one branch =
one PR.

**Prevention:** Before starting a loop, check Cursor usage via `docs/_etc/codexbar.md`, confirm the
slice is not a frozen estimator expansion, and write `_workspace/01_product_command-contract.md`.

## Usage-stop rule (agentic loop)

When weekly (or provider-equivalent) usage is greater than 97% remaining ≤ 3%, wrap the current
slice, open/merge the PR if ready, clear the goal, and stop. Composer/Cursor-model usage is
`codexbar --provider cursor` → `usage.secondary.usedPercent`.

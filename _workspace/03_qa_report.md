# QA Report: `assert` quality gate

## Verdict

`pass` — no blocking cross-boundary mismatch found.

## Boundaries checked

- **Contract → parser:** `assert <boolean-expression>` is executable, requires a predicate, reuses the existing expression grammar, and rejects options, `if`, and assignment syntax.
- **Parser → executor:** `AssertCommand.expression` is dispatched before write/materialization paths; active-dataset requirements and predicate domain validation use existing error semantics.
- **Executor → backend:** DuckDB and Polars-lazy backends return the same `(checked, failed)` aggregate shape; false and missing results fail, empty datasets pass, and failed checks do not replace the active relation.
- **Backend → output:** successful checks produce `AssertResult(checked, failed=0)`, deterministic human text, and the existing versioned JSON envelope; failures use the existing error envelope.
- **CLI/shell/help/docs:** read-only effect metadata, command schema, shell completion, in-app help, command references, language semantics, user guide, README, architecture/spec/changelog are aligned.
- **Tests → claims:** focused coverage includes parser rejection, true/false/missing predicates, unknown/non-boolean expressions, empty data, eager/DuckDB-lazy/Polars-lazy execution, state preservation, human output, JSON success/error, and missing active datasets.

## Evidence

- Full suite: `uv run pytest -q` — 1,310 passed, 320 existing dependency warnings.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright src tests/test_assert.py` — 0 diagnostics.
- `uv run python scripts/check_docs_alignment.py` — passed.
- `verify_code` build, test, and lint stages passed. Its configured mypy stage reports only the known pre-existing untyped third-party imports and duplicate `scripts/check_docs_alignment.py` module discovery.

## Residual risk

Hosted CI and strict MkDocs build were not run locally. Existing project notes record that MkDocs is unavailable in the environment; documentation alignment passed. No implementation blocker remains.

## Recommended next action

Commit and publish this bounded slice as one PR, then stop without starting another feature.

---

# QA Report: `duplicates` quality report

## Verdict

`pass` — no blocking cross-boundary mismatch found for the bounded duplicate-report slice.

## Boundaries checked

- **Contract → parser:** `duplicates`, `duplicates report`, and `duplicates report <varlist>` map to
  one read-only command; quoted `` `report` `` remains a variable; options, `if`, and assignment
  forms are rejected.
- **Parser → executor:** requested/default key variables are preserved, active-dataset requirements
  use existing errors, and dispatch occurs before any write/materialization path.
- **Executor → backend:** DuckDB and Polars-lazy aggregate paths return the same six-count shape;
  null keys group together, empty/no-duplicate inputs are deterministic, and unknown keys preserve
  session state.
- **Backend → output:** `DuplicatesResult` emits the documented human lines and versioned JSON
  envelope; command effect/schema metadata and help use the same syntax.
- **CLI/shell/MCP/docs:** command catalog/effects/schema discovery, `report` and column completion,
  packaged help, unified/indexed references, language semantics, README, architecture/spec/changelog,
  and the MCP data-quality prompt all include the feature.
- **Tests → claims:** focused coverage spans parser rejection, null grouping, default/requested keys,
  empty/no-duplicate cases, state preservation, eager/DuckDB-lazy/Polars-lazy execution, CLI human/
  JSON/error behavior, help/schema, and completions.

## Evidence

- Full suite: `uv run pytest -q` — 1,322 passed, 314 existing dependency warnings.
- Focused suite: `uv run pytest -q tests/test_duplicates.py tests/test_doctor.py tests/test_mcp.py tests/test_shell.py` — 52 passed.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright src` — 0 diagnostics.
- `uv run python scripts/check_docs_alignment.py` — passed.
- `uv build` plus wheel inspection — passed; packaged duplicate help is present.
- `verify_code` — pytest, build, and Ruff passed; mypy remains red only on the documented
  pre-existing untyped imports and duplicate docs-check module discovery.

## Residual risk

The report intentionally has no row-level listing, tagging, dropping, fuzzy matching, or machine
compatibility promise. The repository's configured mypy stage may still report its documented
pre-existing third-party import/module-discovery issues; hosted CI and strict MkDocs builds were not
run locally.

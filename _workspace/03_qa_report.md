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

## Independent review loop

Three local review passes were completed against the base-to-HEAD diff:

1. **Execution correctness:** parser routing, aggregate SQL/Polars metrics, null/empty behavior,
   lazy preservation, and failure/state paths — no actionable findings.
2. **Public contract coherence:** result typing/JSON, CLI effects/schema, completion, help, docs,
   MCP guidance, and roadmap/spec alignment — no actionable findings.
3. **Boundary/edge review:** identifier quoting, SQL injection surface, packaging resources,
   performance shape, and regression coverage — no actionable findings.

## Residual risk

The report intentionally has no row-level listing, tagging, dropping, fuzzy matching, or machine
compatibility promise. The repository's configured mypy stage may still report its documented
pre-existing third-party import/module-discovery issues; hosted CI and strict MkDocs builds were not
run locally.

---

# QA Report: `datasignature`

## Verdict

`pass` — no blocking cross-boundary mismatch found for the bounded reproducibility-fingerprint slice.

## Boundaries checked

- **Contract → parser:** exact no-argument `datasignature` syntax is executable; varlists, options,
  `if`, and assignment forms fail deterministically.
- **Parser → executor:** the typed command is dispatched before mutation paths, requires an active
  dataset, and participates in the existing command-history/error lifecycle.
- **Executor → backend:** public schema and row count are carried into a typed result; eager and
  DuckDB-lazy scans use bounded Arrow batches, while Polars-lazy uses bounded `collect_batches` and
  retains the original lazy plan.
- **Backend → output:** the versioned SHA-256 framing covers ordered public schema and values with
  explicit null/non-finite/temporal/decimal/nested encodings; human and JSON outputs share the same
  `DatasignatureResult`.
- **CLI/shell/help/MCP/docs:** command effects/schema discovery, completion, packaged help, command
  references, language semantics, reproducibility guidance, MCP EDA workflow, README,
  architecture/spec/changelog, and navigation are aligned.
- **Tests → claims:** focused coverage includes exact digest determinism, row-order/schema changes,
  null/non-finite/temporal/decimal values, empty data, state preservation, all execution modes,
  human/JSON/error output, schema/effects/help, and completion.

## Independent review loop

Three local review passes were completed against the complete base-to-HEAD change:

1. **Execution correctness:** parser routing, executor lifecycle, Arrow/Polars scan behavior,
   lazy-plan preservation, error cleanup, and deterministic framing — no actionable findings.
2. **Public contract coherence:** typed model/result union, JSON labels, CLI metadata, help,
   completion, MCP guidance, docs, and roadmap/spec records — no actionable findings.
3. **Boundary/edge review:** identifier quoting, timezone normalization, null/non-finite values,
   nested values, batch memory bounds, row-order sensitivity, and packaging resources — no
   actionable findings.

## Evidence

- `uv run pytest -q` — 1,333 passed, 314 existing dependency warnings.
- Focused command/neighbor suite — 232 passed.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright` on changed source modules — 0 diagnostics.
- `uv run python scripts/check_docs_alignment.py` — passed.
- `uv build` plus wheel inspection — passed; packaged `datasignature` help is present.
- `uv run mkdocs build --strict --site-dir /tmp/tabdat-site-datasignature` — unavailable because
  `mkdocs` is not installed locally.
- `git diff --check` — passed.
- `verify_code` — pytest, build, and Ruff stages passed; configured mypy remains blocked by the
  repository's pre-existing duplicate `scripts/check_docs_alignment.py` module discovery (with
  untyped optional imports reported when that discovery error is bypassed).

## Residual risk

The signature is a TabDat-native logical-data fingerprint, not a byte-level Parquet checksum or a
compatibility implementation of Stata/SAS/SPSS baseline/compare workflows. Hosted CI and strict
MkDocs validation remain external gates; the full repository tests and documentation alignment pass
locally.

---

# QA Report: `gsort`

## Verdict

`pass` — no blocking cross-boundary mismatch found for the bounded directional-sort slice.

## Boundaries checked

- **Contract → parser:** signed keys, omitted ascending prefixes, quoted identifiers, no-argument and
  malformed-key failures, and rejection of options/`if`/assignment forms are aligned.
- **Parser → executor:** typed direction keys are dispatched before mutation; the executor builds a
  stable transform message and preserves existing panel/label metadata behavior.
- **Executor → backend:** direction vectors match key vectors, all variables validate before mutation,
  nulls remain last for both directions, and an ordinal tie-breaker preserves prior order for ties.
- **Backend → output:** existing `TransformResult` semantics are reused for human/JSON output; eager,
  DuckDB-lazy, and Polars-lazy paths share the same key semantics, with Polars remaining lazy.
- **CLI/shell/help/MCP/docs:** effect/schema metadata, command and column completion, packaged help,
  command references, language semantics, user guide, MCP guidance, README, architecture/spec,
  changelog, and navigation are aligned.
- **Tests → claims:** focused coverage includes parser forms, stable mixed-direction/null ordering,
  unknown-variable atomicity, metadata preservation, all execution modes, CLI output/schema/help,
  and completion.

## Independent review loop

Three local review passes were completed against the complete base-to-HEAD change:

1. **Execution correctness:** parser tokenization, direction validation, backend SQL/Polars ordering,
   null placement, tie stability, lazy materialization, and failure state — no actionable findings.
2. **Public contract coherence:** typed command/result surfaces, transform messages, CLI metadata,
   help/completion, MCP guidance, docs, and roadmap/spec alignment — no actionable findings.
3. **Boundary/edge review:** quoted sign-like identifiers, duplicate keys, unknown variables,
   metadata preservation, SQL identifier quoting, and cross-engine output order — no actionable
   findings.

## Evidence

- Focused suite: `uv run pytest -q tests/test_gsort.py tests/test_sort.py tests/test_shell.py tests/test_cli.py tests/test_mcp.py` — 225 passed.
- Full suite: `uv run pytest -q` — 1,341 passed, 314 existing dependency warnings.
- `uv run ruff check .` and `uv run ruff format --check .` — passed on the changed tree.
- `uv run basedpyright` on changed source modules — 0 diagnostics.
- `uv run python scripts/check_docs_alignment.py` — passed.
- `uv build` plus wheel inspection — passed; packaged `gsort` help is present.
- `uv run mkdocs build --strict --site-dir /tmp/tabdat-site-gsort` — unavailable because `mkdocs` is
  not installed locally.
- `git diff --check` — passed.

## Residual risk

`gsort` is intentionally scalar-key-only and does not claim Stata/SAS/SPSS syntax compatibility.
Hosted CI and strict MkDocs validation remain external gates; repository-wide mypy retains its
pre-existing configuration failures.

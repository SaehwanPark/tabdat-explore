# Implementation Report: `assert` quality gate

## Contract consumed

- `_workspace/01_product_command-contract.md`

## Delivered

- Added typed `AssertCommand`/`AssertResult` models and strict `assert <boolean-expression>` parsing.
- Reused TabDat expression inference and compilation so true predicates pass while false or SQL-NULL predicates fail; options, `if`, and assignment forms are rejected.
- Added DuckDB and Polars-lazy aggregate scans with deterministic checked/failed counts. Polars-lazy plans remain active and the command does not mutate dataset/session state.
- Added executor failure handling, human/JSON formatting, read-only CLI effect and command schema metadata, shell completion, help, command references, language semantics, user-guide, architecture, README, `SPEC.md`, and changelog updates.
- Added focused parser, backend/executor, empty-dataset, eager/lazy-engine, state-preservation, CLI text/JSON/error, and active-dataset tests.

## Validation

- `uv run pytest -q` — 1,310 passed, 320 existing dependency warnings.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed (61 files already formatted).
- `uv run basedpyright src tests/test_assert.py` — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed (links, command reference, and help-topic alignment).
- `verify_code` — pytest, build, and Ruff stages passed; configured mypy stage remains red on pre-existing untyped imports (`arviz`, `bambi`, `libpysal`) and duplicate module discovery for `scripts/check_docs_alignment.py`.

## Known limits

`assert` intentionally has no options, `if`, `by`, assignment, row filtering, custom missing-value rules, or row-level diagnostics. Descending/expression sorting and richer workflows remain outside this slice.

---

# Implementation Report: `duplicates` quality report

## Contract consumed

- `_workspace/01_product_command-contract.md` (`duplicates` section)

## Delivered

- Added typed `DuplicatesCommand`/`DuplicatesResult` models and `duplicates [report] [varlist]`
  parsing, including the quoted-identifier escape for a column literally named `report`.
- Added DuckDB and Polars-lazy aggregate duplicate grouping with null-equal key semantics,
  deterministic total/unique/duplicate/surplus/max-copy counts, empty-dataset handling, and no
  active-relation mutation.
- Preserved Polars-lazy plans by allowing duplicate reports through the read-only aggregate path;
  unknown keys fail before any materialization or state update.
- Added executor dispatch, human/JSON formatting, command effect/schema discovery, shell command,
  `report`, and column completions, MCP data-quality prompt guidance, packaged help, command docs,
  language semantics, README, architecture/spec/changelog, and command-reference navigation.
- Fixed environment diagnostics to fall back to `tabdat.__version__` when broken distribution
  metadata returns `None`; added a regression test for that packaging edge case.
- Added focused parser, aggregate backend/executor, null/empty/no-duplicate, eager/DuckDB-lazy/
  Polars-lazy, state-preservation, CLI, schema/help, and shell-completion tests.

## Validation

- `uv run pytest -q` — passed (1,322 tests; 314 existing dependency warnings).
- `uv run pytest -q tests/test_duplicates.py tests/test_doctor.py tests/test_mcp.py tests/test_shell.py` — 52 passed.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed (62 files already formatted).
- `uv run basedpyright src` — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed (links, command reference, and help-topic alignment).
- `uv build` plus wheel inspection — passed; packaged `tabdat/help/topics/duplicates.md` is present.
- `verify_code` — pytest, build, and Ruff stages passed; configured mypy remains red only on the
  repository's pre-existing untyped imports (`arviz`, `bambi`, `libpysal`) and duplicate
  `scripts/check_docs_alignment.py` module discovery.

## Known limits

`duplicates` intentionally reports aggregate counts only. It does not list, tag, or drop duplicate
rows, perform fuzzy/approximate matching, accept row filters/options, or establish a cross-tool
compatibility promise. The existing verification profile's configured mypy stage and hosted CI remain
separate follow-up gates.

---

# Implementation Report: `datasignature`

## Contract consumed

- `_workspace/01_product_command-contract.md` (`datasignature` section)

## Delivered

- Added typed `DatasignatureCommand`/`DatasignatureResult` models and exact no-argument parsing.
- Added a versioned SHA-256 framing algorithm covering canonical public schema, active row order, and
  cell values with explicit null, non-finite, temporal, decimal, binary, and nested-value encodings.
- Added bounded eager/DuckDB-lazy row scans and Polars `collect_batches` scanning while preserving
  the original Polars lazy plan and excluding the internal estimation-sample column.
- Added executor dispatch, deterministic human/JSON formatting, CLI effect/schema discovery, shell
  completion, MCP reproducibility guidance, packaged help, command docs, user-guide guidance,
  language semantics, README, architecture/spec/changelog, and navigation updates.
- Added focused parser, deterministic digest, row-order/schema sensitivity, null/non-finite/temporal/
  decimal cross-engine, empty-dataset, eager/DuckDB-lazy/Polars-lazy, state-preservation, CLI,
  schema/help/effect, and shell-completion coverage.

## Validation

- `uv run pytest -q tests/test_datasignature.py tests/test_duplicates.py tests/test_shell.py tests/test_cli.py tests/test_mcp.py` — 232 passed.
- `uv run pytest -q` — 1,333 passed, 314 existing dependency warnings.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright` on changed source modules — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed (links, command reference, and help-topic alignment).
- `uv build` plus wheel inspection — passed; packaged `tabdat/help/topics/datasignature.md` is present.
- `uv run mkdocs build --strict --site-dir /tmp/tabdat-site-datasignature` — not runnable because
  `mkdocs` is not installed in the current environment.
- `git diff --check` — passed.
- `verify_code` — pytest, build, and Ruff stages passed; the configured mypy stage remains blocked by
  the repository's pre-existing duplicate `scripts/check_docs_alignment.py` module discovery (and
  untyped optional imports when that discovery error is bypassed).

## Known limits

`datasignature` is a TabDat-native logical-data fingerprint, not a byte-level Parquet checksum or a
compatibility implementation of Stata/SAS/SPSS signatures. It intentionally has no stored baseline,
verify/reset subcommands, filtered signatures, algorithm options, metadata-label coverage, or repair
workflow; scripts can persist and compare its JSON signature explicitly.

---

# Implementation Report: `gsort`

## Contract consumed

- `_workspace/01_product_command-contract.md` (`gsort` section)

## Delivered

- Added typed `SortKey`/`GsortCommand` models and signed-key parsing for omitted, `+`, and `-`
  directions, including quoted identifiers and deterministic malformed-key errors.
- Extended the existing stable backend sort with per-key directions, nulls-last behavior, explicit
  ordinal tie-breaking, and command-specific validation/error labels across DuckDB and Polars-lazy.
- Added executor dispatch, metadata preservation, transform messages, CLI effect/schema discovery,
  shell command/column completion, MCP cleaning guidance, packaged help, command docs, user-guide,
  language semantics, README, architecture/spec/changelog, and navigation updates.
- Added focused parser, mixed-direction/stability/null-order, unknown-variable atomicity, metadata,
  eager/DuckDB-lazy/Polars-lazy, CLI human/JSON/schema/help, and shell-completion tests.

## Validation

- `uv run pytest -q tests/test_gsort.py tests/test_sort.py tests/test_shell.py tests/test_cli.py tests/test_mcp.py` — 225 passed.
- `uv run pytest -q` — 1,341 passed, 314 existing dependency warnings.
- `uv run ruff check` on changed source/tests — passed.
- `uv run ruff format --check` on changed source/tests — passed.
- `uv run basedpyright` on changed source modules — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed.
- `uv build` plus wheel inspection — passed; packaged `tabdat/help/topics/gsort.md` is present.
- `uv run mkdocs build --strict --site-dir /tmp/tabdat-site-gsort` — not runnable because `mkdocs`
  is not installed in the current environment.
- `git diff --check` — passed.
- `verify_code` — pytest, build, and Ruff stages passed; configured mypy remains blocked by the
  repository's pre-existing duplicate docs-check module discovery and untyped optional imports.

## Known limits

`gsort` intentionally supports scalar variable keys only. It does not add expression keys, random
ordering, row filters/options, `by:` execution, or a syntax-compatibility promise for Stata, SAS, or
SPSS; existing `sort` remains the ascending-only shorthand.

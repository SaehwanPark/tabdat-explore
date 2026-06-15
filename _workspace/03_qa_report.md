# Enhanced `tabulate` QA Report

## Status

pass

## Boundaries Checked

- Parser contract matches `TabulateCommand` fields for legacy forms, explicit rows/columns,
  command-level `if`, value aggregation, and invalid option combinations.
- Executor and backend agree on dynamic headers plus wide matrix rows for frequency and aggregate
  tabulations.
- `by: tabulate` scopes grouped execution without changing the active dataset path.
- CLI smoke, shell completions, and help topic expose the enhanced command surface.
- SPEC, architecture notes, changelog, README, and command glossary describe the implemented scope
  and keep deferred features out of the current slice.

## Blocking Issues

- None found in focused validation.

## PR Review Loop

- Pass 1 found a compatibility regression: legacy one-way `tabulate` no longer returned
  `Percent`. Fixed in `Preserve one-way tabulate percentages`.
- Pass 2 found absent aggregate pivot cells rendering as `0`, which could fabricate values for
  `mean`, `sum`, `min`, and `max`. Fixed in `Preserve absent aggregate tabulate cells`.
- Pass 3 found `values(x) stat(count)` should keep absent combinations as `0` because it counts
  non-null values. Fixed in `Clarify tabulate count aggregate gaps`.
- Follow-up review after fixes found no remaining Critical or High issues.

## Non-Blocking Follow-Ups

- Add margins/totals and weighted tabulations when the product contract is defined.
- Consider a specialized result model if future table export or richer terminal formatting needs
  metadata beyond flat `TableResult` headers.

## Validation Evidence

- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py tests/test_shell.py tests/test_help.py`
- `uv run ruff check`
- `uv run basedpyright`

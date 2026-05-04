# Phase 6 Visualization Contract

## Request Summary

Add lightweight artifact-based plotting commands while preserving the single active dataset model.

## Roadmap Phase

Phase 6: Visualization System.

## Commands

### `histogram`

Syntax:

```text
histogram <numeric_var>[, bins=<positive_integer> saving(<path>) noopen]
```

- Requires one active dataset and one numeric variable.
- `bins` defaults to Altair's default binning behavior.
- Saves to `artifacts/plots/histogram-<var>.svg` unless `saving(...)` is provided.

### `scatter`

Syntax:

```text
scatter <y_var> <x_var>[, saving(<path>) noopen]
```

- Requires one active dataset and two numeric variables.
- Saves to `artifacts/plots/scatter-<y_var>-<x_var>.svg` unless `saving(...)` is provided.

### `bar`

Syntax:

```text
bar <category_var>[, saving(<path>) missing noopen]
```

- Requires one active dataset and one variable.
- Produces one-way frequency counts.
- Excludes null values by default; `missing` includes them.
- Saves to `artifacts/plots/bar-<category_var>.svg` unless `saving(...)` is provided.

## Artifact Behavior

- Supported output extensions are `.svg` and `.png`.
- Parent directories are created when needed.
- Existing artifact files may be overwritten.
- Successful commands return a concise saved-path result.
- Batch `tabdat -c ...` mode never auto-opens artifacts.
- Interactive shell auto-opens artifacts unless `noopen` is present.

## Non-Goals

- No persistent saved datasets.
- No lazy plotting optimization or downsampling.
- No faceting, grouped plots, custom themes, titles, legends, or aggregate numeric bar charts.
- No configuration for artifact roots.

## Acceptance Criteria

- Focused parser tests cover valid and invalid visualization syntax.
- Focused executor tests verify SVG artifacts are written for all three plot commands.
- CLI smoke tests verify batch plot commands print artifact paths without stderr.
- Shell tests verify completions and auto-open decision behavior without launching external apps.
- Documentation records Phase 6 as complete and notes current limitations.
- Validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`

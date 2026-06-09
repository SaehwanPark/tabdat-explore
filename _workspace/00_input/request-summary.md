# Request Summary: Phase 19 Slice 9 Spatial Weights Configuration & GIS Ingestion

## Goal

Resume development from the latest checkpoint on `main` and implement the Phase 19 spatial weight matrix configuration and GIS file ingestion in `spregress` to support `.gal`, `.gwt`, and `.shp` files (Rook/Queen polygon contiguity weights) alongside matching `predict xb` and `predict spatial_lag` functionality.

## Checkpoint

- Branch base: `main` at latest (`e9d1f1d3f5d747db71980995b407f2c5e3a7ece0`)
- Working branch: `temp/phase19-slice9-spatial-weights-ingestion`
- Prior completed slice: Phase 19 slice 8 (`dml`)

## Touched Surfaces

- Parser (options: `weights()`, `id()`, `contiguity()`)
- Models (`SpregressCommand`, `_SpatialRegressionState`)
- Executor (GIS file reading via libpysal, row/ID alignment, subsetting, prediction routing)
- Formatter, shell completions, help, registry
- Tests and SDD docs (`SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `pyproject.toml`)

## Assumptions

- The ID variable supplied via `id(<id_var>)` maps to keys in `.gal`/`.gwt` files or the shapefile's DBF.
- ID comparison/resolution is case-insensitive for shapefile attributes.
- Missing values in regression sample must trigger subsetting/reordering of the spatial weight matrix to align rows.
- Unsupported formats, missing files, or mismatching IDs raise `ExecutionError`.

## Non-goals

- Out-of-sample prediction.
- resid Moran's I or Lagrange Multiplier diagnostics.

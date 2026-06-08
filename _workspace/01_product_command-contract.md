# Phase 19 Slice 9 Command Contract: `spregress` Spatial Weights Configuration & GIS Ingestion

## Roadmap Phase

- Phase 19 modern extensions
- Spatial weight matrix configuration and GIS file ingestion

## Syntax

```stata
spregress <y> <xvars>, weights(<path>) id(<id_var>) [contiguity(queen|rook)] [options...]
```

## Behavior

- Mutual exclusivity: either `coord()` or `weights()` option is allowed, but not both.
- `weights(path)` specifies the path to a `.gal`, `.gwt`, or `.shp` file.
- `id(id_var)` specifies the dataset variable containing matching IDs for the spatial weights matrix.
- `contiguity(queen|rook)` specifies shapefile contiguity (Queen by default, Rook optional); ignored for `.gal` and `.gwt` files.
- The executor loads the spatial weights matrix from the GIS file using `libpysal.io.open` or `libpysal.weights.Queen/Rook`.
- The loaded matrix is subsetted and reordered (aligned) to match the cleaned regression sample (handling observations dropped due to missing values).
- The matrix is row-standardized (standard behavior).

## Option Rules

- `weights` requires `id`.
- `contiguity` requires `weights`.
- `weights` cannot coexist with `coord` or `knn`.

## Acceptance Criteria

- Parser rejects invalid combinations of `coord` and `weights`.
- Executor supports `.gal`, `.gwt`, and `.shp` files correctly.
- Aligns spatial weights to the active dataset's rows (matching the regression sample subset).
- Triggers `ExecutionError` for missing files, unsupported formats, or missing/mismatching IDs.
- Full validation suite passes.

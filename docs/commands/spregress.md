# `spregress`

Fit a Maximum Likelihood or GMM spatial autoregressive lag, spatial error, or combo (SARAR/SAC) model using on-the-fly row-standardized KNN spatial weight matrices constructed from coordinates or pre-computed weights files (supports .gal, .gwt, and .shp).

!!! question "When to use"
    How do I model spatial dependencies and spatial autocorrelation in my data using coordinates or pre-computed spatial weight matrices?

## Syntax

```text
spregress y xvars, coord(lat_var lon_var) [model(lag|error|sarar) knn(<k>) robust]
spregress y xvars, weights(weights_file) id(id_var) [contiguity(queen|rook) model(lag|error|sarar) robust]
```

## Examples

```text
spregress price size rooms, coord(lat lon)
spregress price size rooms, coord(lat lon)` then `predict price_full, spatial_lag
spregress price size rooms, coord(lat lon) model(error) knn(8)
spregress price size rooms, coord(lat lon) model(sarar)
spregress price size rooms, weights(w.gal) id(station) model(sarar) robust
spregress price size rooms, weights(w.gal) id(station)
spregress price size rooms, weights(columbus.shp) id(polyid) contiguity(rook)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

# spregress

How to invoke:
`spregress y xvars, coord(lat_var lon_var) [model(lag|error) knn(<k>) robust]`
`spregress y xvars, weights(weights_file) id(id_var) [contiguity(queen|rook) model(lag|error) robust]`

What it does:
Fit a Maximum Likelihood or GMM spatial autoregressive lag or spatial error model using on-the-fly row-standardized KNN spatial weight matrices constructed from coordinates or pre-computed weights files (supports .gal, .gwt, and .shp).

What problem it answers:
How do I model spatial dependencies and spatial autocorrelation in my data using coordinates or pre-computed spatial weight matrices?

Examples:
- `spregress price size rooms, coord(lat lon)`
- `spregress price size rooms, coord(lat lon)` then `predict price_full, spatial_lag`
- `spregress price size rooms, coord(lat lon) model(error) knn(8)`
- `spregress price size rooms, weights(w.gal) id(station)`
- `spregress price size rooms, weights(columbus.shp) id(polyid) contiguity(rook)`

Links:
- `docs/microecometrics_topics.md`

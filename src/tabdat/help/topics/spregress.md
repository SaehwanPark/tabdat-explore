# spregress

How to invoke:
`spregress y xvars, coord(lat_var lon_var) [model(lag|error) knn(<k>) robust]`

What it does:
Fit a Maximum Likelihood or GMM spatial autoregressive lag or spatial error model using on-the-fly row-standardized KNN spatial weight matrices.

What problem it answers:
How do I model spatial dependencies and spatial autocorrelation in my data using coordinates?

Examples:
- `spregress price size rooms, coord(lat lon)`
- `spregress price size rooms, coord(lat lon) model(error) knn(8)`
- `spregress price size rooms, coord(lat lon) robust`

Links:
- `docs/microecometrics_topics.md`

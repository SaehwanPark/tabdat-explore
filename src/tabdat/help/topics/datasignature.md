# datasignature

Compute a deterministic SHA-256 fingerprint of the active dataset for reproducibility checks.

## Syntax

```text
datasignature
```

The signature covers public column names and logical types, active row order, and every cell value.
Nulls and non-finite values have explicit encodings. Session-local labels, panel metadata, source
paths, and execution engines are not included. The command is read-only and accepts no varlist,
options, `if` clause, assignment, or `by:` prefix.

```text
tabdat> use survey.parquet, lazy engine=polars
tabdat> datasignature
Data signature
Algorithm: sha256
Rows: 3
Columns: 4
Signature: <64 lowercase hexadecimal characters>
```

Equivalent active data loaded eagerly, through DuckDB-lazy, or through Polars-lazy produces the same
TabDat-native signature. The scan preserves a Polars lazy plan; it does not compute a Parquet byte
checksum or promise compatibility with other statistical packages' signatures.

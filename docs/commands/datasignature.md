# `datasignature`

`datasignature` computes a deterministic, TabDat-native SHA-256 fingerprint of the active dataset.
It is useful for recording a reproducibility baseline before a scripted analysis or checking whether
a data preparation step changed the values or schema.

## Syntax

```text
datasignature
```

The command accepts no varlist, options, `if` clause, assignment, or `by:` prefix.

## What is covered

The versioned signature includes:

- public column names and canonicalized logical types, in schema order;
- active row order; and
- every cell value, including explicit null and non-finite-value encodings.

It excludes session-local labels, panel metadata, source paths, backend choice, and execution mode.
This is a TabDat-native data fingerprint, not a byte-for-byte Parquet checksum or a compatibility
promise for Stata, SAS, or SPSS signatures.

## Execution behavior

The command is read-only. Eager and DuckDB-lazy data are scanned in bounded row batches. Polars-lazy
uses bounded `collect_batches` scans and keeps the existing lazy plan active. The active dataset,
labels, panel metadata, named tables, and materialization state are unchanged.

## Output

Human output reports the algorithm, scanned row count, public-column count, and a 64-character
lowercase hexadecimal signature:

```text
Data signature
Algorithm: sha256
Rows: 3
Columns: 4
Signature: 3b7e...
```

JSON output uses `DatasignatureResult`:

```json
{
  "schema_version": 1,
  "result_type": "DatasignatureResult",
  "data": {
    "algorithm": "sha256",
    "signature": "3b7e...",
    "row_count": 3,
    "column_count": 4
  }
}
```

An empty dataset is valid and returns zero rows with a schema-dependent signature. Running the
command without an active dataset uses the standard no-active-dataset error.

## Examples

```text
use data/analytic.parquet, lazy engine=polars
datasignature
```

Save the JSON `signature` in a run manifest and compare it before rerunning an analysis. A changed
value, null, schema, or row order produces a different signature.

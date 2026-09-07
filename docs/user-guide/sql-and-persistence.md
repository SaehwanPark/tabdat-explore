# SQL & Persistence

TabDat integrates DuckDB SQL directly into the interactive session and script workflows, providing an escape hatch for ad-hoc queries, joins, and window functions.

---

## The `sql` Command

The active dataset is exposed to SQL queries under the table name `active`:

```text
tabdat> sql select sex, avg(bmi) as avg_bmi from active group by sex
sex  avg_bmi
F    24.8
M    26.2
```

---

## Creating Named Tables with `into <table>`

You can direct the output of any SQL query into a session-local named table:

```text
tabdat> sql select age, avg(income) as mean_income from active group by age order by age into age_summary
Created age_summary: 45 rows, 2 columns
```

This creates `age_summary` in memory and makes it the active dataset. You can return to it later via `use age_summary`.

---

## Persistence: `save` and `export`

To persist the active dataset to disk as a standard Apache Parquet file, use `save` or `export`:

```text
tabdat> save cleaned_cohort.parquet
Saved: cleaned_cohort.parquet (15000 rows, 12 columns)
```

### Overwrite Protection
If the destination file already exists, TabDat prevents accidental overwrites unless you explicitly supply `, replace`:

```text
tabdat> save cleaned_cohort.parquet, replace
Overwritten: cleaned_cohort.parquet (15000 rows, 12 columns)
```

## Reusing data-dictionary labels

Variable labels and value-label sets can be saved separately as a deterministic, versioned TabDat JSON
file and applied to another active dataset with matching columns:

```text
tabdat> label save labels.json, replace
Saved label dictionary: labels.json
tabdat> label use labels.json
Loaded label dictionary: labels.json
```

`label use` validates every variable and value-label attachment before changing the active metadata.
Malformed dictionaries and mismatched datasets fail atomically. This JSON format is TabDat-native; it
is inspired by familiar Stata/SAS/SPSS data-dictionary workflows and is not a claim of direct native
`.dta`, SAS catalog, or `.sav` compatibility.

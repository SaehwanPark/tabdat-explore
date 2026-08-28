# Sessions and the Data Model

TabDat operates around an in-memory session model designed for speed, safety, and predictability.

---

## The Active Dataset

At any given time, a TabDat session maintains **one active dataset**. All standard inspection, transformation, modeling, and plotting commands operate directly on this active dataset.

When you execute a transformation (such as `generate`, `replace`, `keep`, `drop`, or `rename`), TabDat updates the active dataset relation:

```text
tabdat> use patients.parquet
Loaded: patients.parquet (1200 rows, 5 columns)

tabdat> generate bmi = weight / (height / 100)^2
Generated: bmi (DOUBLE)
```

---

## Session-Local Named Tables

In addition to the active dataset, a session can maintain named tables in memory.

### Creating Named Tables via SQL
Use the `into <table>` clause in SQL commands to store query results into a named table:

```text
tabdat> sql select sex, avg(bmi) as mean_bmi from active group by sex into summary_by_sex
Created summary_by_sex: 2 rows, 2 columns
```

When created, the new named table immediately becomes the active dataset.

### Switching Between Tables
You can switch back to any named table using `use <table>`:

```text
tabdat> use summary_by_sex
Activated: summary_by_sex (2 rows, 2 columns)
```

Named tables exist purely in memory for the duration of the CLI session. To persist them, use `save` or `export`.

---

## Panel Metadata

Panel data structures are defined using `panel <id_var> <time_var>`:

```text
tabdat> panel id year
Panel declared: id=id, time=year (balanced panel: 500 units x 10 periods)
```

- **Integrity Requirements**: The `(id, time)` pair must have zero missing values and must uniquely identify every row.
- **Scope**: Panel metadata is session-local and retained in memory.
- **Dependent Commands**: Panel-aware commands such as `xtreg`, `xtdata`, `xtlogit`, `xtabond`, and panel `did` require active panel metadata.
- **Clearing Panel Metadata**: Run `panel clear` to remove panel declarations.

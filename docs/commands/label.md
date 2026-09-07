# `label`

Manage variable labels and named value-label dictionaries on the active dataset.

## Syntax

```text
label variable <varname> "text"
label variable <varname>, clear
label define <lblname> <value> "text" ... [, replace]
label values <varname> <lblname>
label values <varname>, clear
label list [<lblname> ...]
label drop <lblname> ...
label save <path> [, replace]
label use <path>
```

## Data-dictionary files

`label save` writes a deterministic, versioned TabDat JSON dictionary. `label use` validates the
schema and every variable/value-label attachment before replacing active metadata. The format is
TabDat-native and is not a direct Stata `.dta`, SAS catalog, or SPSS `.sav` compatibility layer.

```text
label variable age "Age in years"
label define sexlbl 0 "Male" 1 "Female"
label values sex sexlbl
label save labels.json, replace
label use labels.json
```

Use `label list` to inspect the current dictionary. `describe`, `codebook`, and `tabulate` consume
attached labels; `tabulate ..., nolabel` displays raw category codes.

## See also

- [Command Reference Index](../command-reference/index.md)
- [SQL & Persistence](../user-guide/sql-and-persistence.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)

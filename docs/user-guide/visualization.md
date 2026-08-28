# Visualization & Artifacts

TabDat follows a **terminal-first, silent-by-default** visualization philosophy. Plots are rendered into clean static image artifacts (PNG, SVG, PDF) and saved to disk without popping intrusive GUI windows.

---

## Plot Commands

### 1. Histogram (`histogram`)
Plot the empirical distribution of a continuous variable:

```text
tabdat> histogram income
Plot saved: artifacts/plots/histogram-income.png
file:///Users/username/project/artifacts/plots/histogram-income.png
```

Specify custom bins or frequency mode:
```text
tabdat> histogram income, bins(30) freq
```

### 2. Scatter Plot (`scatter`)
Generate a bivariate scatter plot with optional fit line:

```text
tabdat> scatter income age
Plot saved: artifacts/plots/scatter-income-age.png
```

### 3. Categorical Bar Chart (`bar`)
Display frequency distributions for categorical variables:

```text
tabdat> bar education_level
Plot saved: artifacts/plots/bar-education_level.png
```

Include missing categories with `, missing`:
```text
tabdat> bar education_level, missing
```

### 4. Bayesian MCMC Diagnostics (`bayesplot`)
Generate MCMC diagnostic plots after fitting a `bayes:` model:

```text
tabdat> bayes: regress wage educ exper
tabdat> bayesplot trace
tabdat> bayesplot density
tabdat> bayesplot autocorrelation
```

---

## Plot Settings & Configuration

| Setting | Values | Default | Description |
|---|---|---|---|
| `graph_format` | `png`, `svg`, `pdf` | `png` | Image file format for saved plots. |
| `artifact_dir` | Path string | `artifacts` | Root directory for plot and report artifacts. |
| `graph_open` | `true`, `false` | `false` | If `true`, automatically launches system image viewer. |

Change settings interactively with `set`:
```text
tabdat> set graph_format svg
tabdat> set artifact_dir figures
tabdat> set graph_open false
```

Or pass explicit output paths using `saving(...)`:
```text
tabdat> histogram age, saving(figures/age_dist.svg)
```

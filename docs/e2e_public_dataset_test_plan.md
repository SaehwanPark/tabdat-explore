# Public-Dataset Integrated E2E Test Plan

This document defines integrated, public-dataset end-to-end scenarios for TabDat-Explore across
Phases 1 through 9. The scenarios are written for AI agents and keep success criteria machine-
observable: exit codes, stdout substrings or regexes, stderr expectations, and file existence at
fixed paths.

## Coverage Matrix

| Scenario | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 | Phase 8 | Phase 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `s1_titanic_batch_core` | yes | yes | yes | no | no | no | no | no | no |
| `s2_interactive_shell_contract` | yes | no | yes | yes | yes | yes | no | no | no |
| `s3_taxi_lazy_scale` | yes | no | yes | yes | no | yes | yes | no | yes |
| `s4_penguins_script_repro` | yes | yes | yes | yes | no | yes | no | yes | yes |

## Global Harness Rules

```yaml
harness:
  repo_cwd: /Users/saehwan/repos/tabdat-explore-dev
  shell: zsh
  install_command: uv sync
  artifact_root: artifacts/e2e
  stdout_capture: required
  stderr_capture: required
  exit_code_capture: required
  file_existence_checks: required
  file_content_checks:
    - svg_files_must_start_with: "<svg"
    - parquet_files_must_exist: true
  forbidden_actions:
    - do_not_modify_src
    - do_not_modify_tests
    - do_not_treat_terminal_color_as_pass_fail
```

## Dataset Acquisition Manifest

```yaml
datasets:
  - dataset_id: titanic
    source_kind: csv
    source_url: https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv
    source_license_note: seaborn sample dataset
    local_csv_path: artifacts/e2e/data/titanic.csv
    local_parquet_path: artifacts/e2e/data/titanic.parquet
    fetch_command: >
      curl -L https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv
      -o artifacts/e2e/data/titanic.csv
    convert_command: >
      uv run python -c "from pathlib import Path; import duckdb, sys;
      src=Path(sys.argv[1]); dst=Path(sys.argv[2]); dst.parent.mkdir(parents=True, exist_ok=True);
      con=duckdb.connect();
      con.execute('copy (select * from read_csv_auto(?)) to ? (format parquet)', [str(src), str(dst)]);
      con.close()"
      artifacts/e2e/data/titanic.csv artifacts/e2e/data/titanic.parquet
  - dataset_id: penguins
    source_kind: csv
    source_url: https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv
    source_license_note: seaborn sample dataset
    local_csv_path: artifacts/e2e/data/penguins.csv
    local_parquet_path: artifacts/e2e/data/penguins.parquet
    fetch_command: >
      curl -L https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv
      -o artifacts/e2e/data/penguins.csv
    convert_command: >
      uv run python -c "from pathlib import Path; import duckdb, sys;
      src=Path(sys.argv[1]); dst=Path(sys.argv[2]); dst.parent.mkdir(parents=True, exist_ok=True);
      con=duckdb.connect();
      con.execute('copy (select * from read_csv_auto(?)) to ? (format parquet)', [str(src), str(dst)]);
      con.close()"
      artifacts/e2e/data/penguins.csv artifacts/e2e/data/penguins.parquet
  - dataset_id: nyc_taxi_jan_2023
    source_kind: parquet
    source_url: https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet
    provenance_url: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
    local_parquet_path: artifacts/e2e/data/yellow_tripdata_2023-01.parquet
    fetch_command: >
      curl -L https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet
      -o artifacts/e2e/data/yellow_tripdata_2023-01.parquet
```

## Scenario Definitions

### `s1_titanic_batch_core`

```yaml
scenario_id: s1_titanic_batch_core
goal: Cover the core eager-load and first-pass EDA flow in batch mode.
phases: [1, 2, 3]
mode: batch_c
dataset:
  dataset_id: titanic
  local_path: artifacts/e2e/data/titanic.parquet
preflight:
  - uv sync
  - mkdir -p artifacts/e2e/data artifacts/e2e/s1
  - dataset fetch and parquet conversion must succeed
command:
  argv:
    - uv
    - run
    - tabdat
    - -c
    - use artifacts/e2e/data/titanic.parquet
    - -c
    - describe
    - -c
    - summarize age fare sibsp parch
    - -c
    - codebook sex class deck embarked survived
    - -c
    - count
    - -c
    - head 5
    - -c
    - tail 5
    - -c
    - keep if age >= 18
    - -c
    - drop deck alone
    - -c
    - rename sex gender
    - -c
    - generate family_size = sibsp + parch + 1
    - -c
    - replace fare = 0 if fare < 1
    - -c
    - select survived pclass class gender age fare family_size
    - -c
    - tabulate gender survived, row col missing
    - -c
    - by pclass: summarize age fare
    - -c
    - collapse mean age fare, by(survived)
    - -c
    - head 5
expected_exit_code: 0
expected_stdout_contains:
  - "Loaded: artifacts/e2e/data/titanic.parquet"
  - "Rows:"
  - "Variable  Type"
  - "Variable  Count  Mean"
  - "Variable  Type  Nonmissing  Missing  Distinct  Examples"
  - "Kept matching rows:"
  - "Dropped selected columns:"
  - "Renamed sex to gender:"
  - "Generated family_size:"
  - "Replaced fare:"
  - "Selected columns:"
  - "gender"
  - "survived"
  - "row_percent"
  - "column_percent"
  - "pclass"
  - "Collapsed dataset:"
expected_stdout_regex:
  - "Rows: [0-9]+"
  - "Collapsed dataset: [0-9]+ rows, 3 columns"
expected_stderr: ""
expected_files: []
red_flags:
  - any stderr output
  - parse error around if clauses, by clauses, or comma options
  - final preview still includes dropped columns
  - generated family_size column absent after select
  - collapse result does not reduce to survived plus aggregated columns
```

### `s2_interactive_shell_contract`

```yaml
scenario_id: s2_interactive_shell_contract
goal: Cover prompt-toolkit shell behavior that is observable through TTY interaction.
phases: [1, 3, 4, 5, 6]
mode: interactive_tty
dataset:
  dataset_id: titanic
  local_path: artifacts/e2e/data/titanic.parquet
preflight:
  - uv sync
  - dataset fetch and parquet conversion must succeed
  - remove ~/.tabdat_history before the scenario if isolation is required
interactive_steps:
  - send: "use artifacts/e2e/data/titanic.parquet\n"
  - expect_stdout_contains: ["Loaded: artifacts/e2e/data/titanic.parquet"]
  - send: "summarize a\t"
  - expect_buffer_contains: ["summarize age"]
  - send: "\u0003"
  - send: "tabulate sex, \t"
  - expect_buffer_contains: ["row", "col", "missing"]
  - send: "\u0003"
  - send: "by s\t"
  - expect_buffer_contains: ["by sex"]
  - send: "\u0003"
  - send: "by sex: sum\t"
  - expect_buffer_contains: ["by sex: summarize"]
  - send: "\u0003"
  - send: "sql group\t"
  - expect_buffer_contains: ["sql group by"]
  - send: "\u0003"
  - send: "histogram a\t"
  - expect_buffer_contains: ["histogram age"]
  - send: "\u0003"
  - send: "count\n"
  - expect_stdout_regex: ["Rows: [0-9]+"]
  - send: "exit\n"
history_reopen_check:
  - reopen_shell: true
  - send: "\u001b[A"
  - expect_buffer_contains: ["count"]
  - filesystem_check:
      path: ~/.tabdat_history
      must_exist: true
      must_contain: ["use artifacts/e2e/data/titanic.parquet", "count"]
expected_exit_code: 0
expected_stderr: ""
expected_files:
  - "~/.tabdat_history"
red_flags:
  - empty column completion after dataset load
  - options missing after a trailing comma
  - by-child completion missing after colon
  - history not persisted across sessions
  - shell becomes unresponsive after completion or interrupt
notes:
  - syntax coloring is not a pass/fail signal
  - buffer checks require a TTY-aware harness, not plain stdout-only execution
```

### `s3_taxi_lazy_scale`

```yaml
scenario_id: s3_taxi_lazy_scale
goal: Cover the real lazy-load path on a larger public dataset, with SQL, plots, and persistence.
phases: [1, 3, 4, 6, 7, 9]
mode: batch_c
dataset:
  dataset_id: nyc_taxi_jan_2023
  local_path: artifacts/e2e/data/yellow_tripdata_2023-01.parquet
preflight:
  - uv sync
  - mkdir -p artifacts/e2e/data artifacts/e2e/s3
  - dataset fetch must succeed
command:
  argv:
    - uv
    - run
    - tabdat
    - -c
    - use artifacts/e2e/data/yellow_tripdata_2023-01.parquet, lazy engine=duckdb
    - -c
    - describe
    - -c
    - count
    - -c
    - select passenger_count trip_distance fare_amount tip_amount total_amount payment_type
    - -c
    - keep if trip_distance >= 10
    - -c
    - drop if fare_amount == 0
    - -c
    - generate tip_share = tip_amount / total_amount
    - -c
    - summarize trip_distance fare_amount tip_amount total_amount tip_share
    - -c
    - sql select payment_type, avg(total_amount) as mean_total, avg(tip_share) as mean_tip_share from active group by payment_type order by payment_type
    - -c
    - histogram total_amount, bins=30 saving(artifacts/e2e/s3/total_amount_hist.svg) noopen
    - -c
    - bar payment_type, missing saving(artifacts/e2e/s3/payment_type_bar.svg) noopen
    - -c
    - save artifacts/e2e/s3/filtered_trips.parquet, replace
    - -c
    - sql select payment_type, count(*) as n from active group by payment_type order by payment_type into payment_summary
    - -c
    - head 10
expected_exit_code: 0
expected_stdout_contains:
  - "Loaded: artifacts/e2e/data/yellow_tripdata_2023-01.parquet (unknown rows,"
  - "lazy=duckdb"
  - "Rows:"
  - "Selected columns:"
  - "Kept matching rows:"
  - "Dropped matching rows:"
  - "Generated tip_share:"
  - "payment_type"
  - "mean_total"
  - "mean_tip_share"
  - "Saved plot: artifacts/e2e/s3/total_amount_hist.svg"
  - "Saved plot: artifacts/e2e/s3/payment_type_bar.svg"
  - "Saved: artifacts/e2e/s3/filtered_trips.parquet"
  - "Created payment_summary:"
expected_stdout_regex:
  - "Rows: [0-9]+"
  - "Saved: artifacts/e2e/s3/filtered_trips.parquet \\([0-9]+ rows, 7 columns\\)"
expected_stderr: ""
expected_files:
  - artifacts/e2e/s3/total_amount_hist.svg
  - artifacts/e2e/s3/payment_type_bar.svg
  - artifacts/e2e/s3/filtered_trips.parquet
followup_probe:
  argv:
    - uv
    - run
    - tabdat
    - -c
    - use artifacts/e2e/data/yellow_tripdata_2023-01.parquet, lazy engine=polars
    - -c
    - count
    - -c
    - head 2
  expected_exit_code: 0
  expected_stdout_contains:
    - "Loaded: artifacts/e2e/data/yellow_tripdata_2023-01.parquet (unknown rows,"
    - "lazy=polars"
    - "Rows:"
  expected_stderr: ""
red_flags:
  - initial lazy load prints a numeric row count instead of unknown rows
  - batch mode attempts to auto-open plots
  - save output is not Parquet-backed
  - sql into does not replace the active dataset used by the final head
  - polars selector is accepted but not reflected in the load banner
```

### `s4_penguins_script_repro`

```yaml
scenario_id: s4_penguins_script_repro
goal: Cover reproducible script execution, nested run, config loading, SQL multiline blocks, plots, and export.
phases: [1, 2, 3, 4, 6, 8, 9]
mode: script_file
dataset:
  dataset_id: penguins
  local_path: artifacts/e2e/data/penguins.parquet
preflight:
  - uv sync
  - mkdir -p artifacts/e2e/data artifacts/e2e/s4
  - dataset fetch and parquet conversion must succeed
  - write config and script files exactly as defined below
files_to_create:
  - path: artifacts/e2e/s4/config.tabdat.toml
    content: |
      graph_format = "png"
      artifact_dir = "artifacts/e2e/s4/artifacts"
      graph_open = false
  - path: artifacts/e2e/s4/prep.td
    content: |
      summarize bill_length_mm flipper_length_mm body_mass_g
      generate body_mass_kg = body_mass_g / 1000
      scatter body_mass_g flipper_length_mm, saving(artifacts/e2e/s4/artifacts/plots/penguins_scatter.png) noopen
  - path: artifacts/e2e/s4/analysis.td
    content: |
      use artifacts/e2e/data/penguins.parquet
      run prep.td
      tabulate species sex, row col missing
      sql """
      select
        species,
        avg(body_mass_kg) as mean_body_mass_kg,
        avg(flipper_length_mm) as mean_flipper_length_mm
      from active
      group by species
      order by species
      """ into penguin_summary
      head 10
      export artifacts/e2e/s4/penguin_summary.parquet, replace
command:
  argv:
    - uv
    - run
    - tabdat
    - --config
    - artifacts/e2e/s4/config.tabdat.toml
    - -f
    - artifacts/e2e/s4/analysis.td
expected_exit_code: 0
expected_stdout_contains:
  - "Script: artifacts/e2e/s4/analysis.td"
  - "TabDat:"
  - "Python:"
  - "Config: graph_format=png, artifact_dir=artifacts/e2e/s4/artifacts, graph_open=off"
  - ". use artifacts/e2e/data/penguins.parquet"
  - "Script: artifacts/e2e/s4/prep.td"
  - ". summarize bill_length_mm flipper_length_mm body_mass_g"
  - "Generated body_mass_kg:"
  - "Saved plot: artifacts/e2e/s4/artifacts/plots/penguins_scatter.png"
  - "species"
  - "row_percent"
  - "column_percent"
  - "Created penguin_summary:"
  - "Saved: artifacts/e2e/s4/penguin_summary.parquet"
expected_stdout_regex:
  - "Saved: artifacts/e2e/s4/penguin_summary.parquet \\([0-9]+ rows, 3 columns\\)"
expected_stderr: ""
expected_files:
  - artifacts/e2e/s4/config.tabdat.toml
  - artifacts/e2e/s4/prep.td
  - artifacts/e2e/s4/analysis.td
  - artifacts/e2e/s4/artifacts/plots/penguins_scatter.png
  - artifacts/e2e/s4/penguin_summary.parquet
red_flags:
  - script metadata missing or reordered unexpectedly
  - nested run fails to resolve relative paths
  - plot auto-open occurs in script mode
  - multiline sql block parse fails
  - exported parquet is missing after a successful exit code
```

## Global Red Flags

```yaml
global_red_flags:
  - parser accepts a command that executor cannot honor without a clear user-facing error
  - lazy-load output stops being honest about unknown initial row counts
  - batch and script modes diverge on artifact naming or config behavior
  - script transcripts become nondeterministic across repeated runs with the same inputs
  - active-dataset replacement after collapse or sql into is not visible in subsequent commands
```

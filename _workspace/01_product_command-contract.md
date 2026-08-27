# Product Contract: Silent Plot Drawing & Clickable File Links

## Request Summary
1. Make plot generation silent by default without popping open browser or external viewer windows.
2. Output clickable `file://<path>` URIs for plot results so users can easily click or open them on demand.
3. Guarantee that test suites never open browser / external viewer windows.

## Roadmap Phase
Cross-phase UX & Tooling Stabilization.

## Invocation & Semantics Rules

### 1. Default Configuration (`graph_open = False`)
- Default `graph_open` in `TabDatConfig` is `False` (`off`).
- In interactive shell mode (`tabdat`), plots are saved silently without launching the platform opener command (`open`, `xdg-open`, `os.startfile`).
- Setting `set graph_open on` in an interactive session or setting `graph_open = true` in config file retains the ability to opt into auto-opening.

### 2. Plot Result Formatting
- Terminal output for `PlotResult` formats the saved path as a fully resolved RFC 8089 `file://` URI:
  `Saved plot: <file_uri>`
  Example:
  `Saved plot: file:///Users/username/project/artifacts/plots/histogram-age.svg`
- For machine JSON output (`--json`), `PlotResult` data envelope retains the structured fields `{"path": "...", "should_open": ...}` for machine consumption.

### 3. Test Isolation Guarantee
- The test harness in `tests/conftest.py` installs an autouse fixture ensuring that no platform opener (`tabdat.cli._open_path`) executes external processes during test runs.

## Examples
Terminal output:
```text
. histogram age
Saved plot: file:///Users/username/repo/artifacts/plots/histogram-age.svg
```

Configuration banner in script runs:
```text
Config: graph_format=svg, artifact_dir=artifacts, graph_open=off
```

## Acceptance Criteria
- [ ] `TabDatConfig.graph_open` defaults to `False`.
- [ ] `format_result(PlotResult(...))` outputs `Saved plot: file://...`.
- [ ] `tests/conftest.py` prevents browser/opener execution across the entire test suite.
- [ ] All CLI, config, and E2E tests pass without opening browser/preview windows.
- [ ] Documentation and help topics reflect `graph_open = off` default and `file://` link output.

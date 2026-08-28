# Configuration

TabDat supports runtime session configuration, project-level `.tabdat.toml` files, and user-level XDG global settings.

---

## Precedence Hierarchy

Configuration values are resolved in the following priority (highest to lowest):

1. **CLI Flags**: Explicit command-line arguments (e.g. `--config custom.toml`).
2. **Project Config**: `.tabdat.toml` located in the current working directory.
3. **User Global Config**: `~/.config/tabdat/config.toml` (or `$XDG_CONFIG_HOME/tabdat/config.toml`).
4. **Internal Defaults**: Built-in defaults (`graph_format="png"`, `artifact_dir="artifacts"`, `graph_open=false`).

---

## Configuration Keys

| Key | Type | Default | Description |
|---|---|---|---|
| `graph_format` | `string` | `"png"` | Plot output format (`"png"`, `"svg"`, `"pdf"`). |
| `artifact_dir` | `string` | `"artifacts"` | Directory for saved plot and report artifacts. |
| `graph_open` | `boolean` | `false` | Whether to automatically open plots in default GUI viewer. |

---

## Example `.tabdat.toml`

```toml
# .tabdat.toml (Project Root)
graph_format = "svg"
artifact_dir = "output/figures"
graph_open = false
```

Load a specific configuration file when executing scripts:

```bash
tabdat --config production.toml -f pipeline.td
```

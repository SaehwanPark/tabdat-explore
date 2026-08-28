# Installation

TabDat-Explore supports macOS (Apple Silicon & Intel) and Linux x86_64 / aarch64.

---

## Recommended: One-Line Installer

Install TabDat globally in seconds:

```bash
curl -LsSf https://raw.githubusercontent.com/SaehwanPark/tabdat-explore/main/scripts/install.sh | sh
```

The installer verifies Python 3.13, fetches the latest distribution wheel, installs the standalone `tabdat` and `tabdat-mcp` executables into `~/.local/bin`, and verifies the installation with `tabdat doctor`.

---

## Homebrew (macOS & Linux)

```bash
brew tap SaehwanPark/tabdat https://github.com/SaehwanPark/tabdat-explore.git
brew install tabdat
```

---

## Using `uv tool`

If you use [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/SaehwanPark/tabdat-explore.git
```

This makes `tabdat` and `tabdat-mcp` available globally in your PATH.

---

## Building from Source

```bash
# Clone repository
git clone https://github.com/SaehwanPark/tabdat-explore.git
cd tabdat-explore

# Install dependencies and sync environment
uv sync

# Run TabDat
uv run tabdat
```

---

## System Diagnostics

After installation, verify your environment and installed backend engines with `doctor`:

```bash
tabdat doctor
```

For automated checks, `tabdat --json doctor` outputs machine-readable JSON envelopes.

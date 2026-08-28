# Request Summary: GitHub Pages Documentation Migration & Deployment

## 1. Goal
Refine, modernize, and migrate all user manuals, guides, command references, and architecture specifications into a production-grade, fast, searchable, and responsive GitHub Pages documentation site hosted at `https://saehwanpark.github.io/tabdat-explore/`. Follow with full validation, pull request handoff, and autonomous merge into `main`.

## 2. Touched Surfaces
- `pyproject.toml`: Added `docs` dependency group (`mkdocs-material>=9.5.0`, `pymdown-extensions>=10.7`), updated Documentation URL to GitHub Pages URL, excluded `/site` from sdist.
- `mkdocs.yml`: Complete configuration for Material for MkDocs (themes, dark/light palette switcher, search, tabs, code annotations, comprehensive navigation across all 69 commands and guides).
- `docs/`: Full documentation hierarchy:
  - `docs/index.md`: Modern landing page with interactive badges, highlights, terminal demos, quick install snippets.
  - `docs/getting-started/`: Modular guides for installation, interactive shell, and quickstart tutorial.
  - `docs/user-guide/`: Modular guides for sessions & data model, loading & diagnostics, scripting & automation, estimation workflows, visualization, SQL & persistence, and configuration.
  - `docs/command-reference/`: Categorized index and command reference overview.
  - `docs/commands/`: 69 dedicated, individual markdown pages for every command and topic.
  - `docs/contributing.md`, `docs/architecture.md`, `docs/roadmap.md`: Adapted repository guides.
- `.github/workflows/pages.yml`: Automated GitHub Pages build and deployment workflow using GitHub Actions (`build_type: workflow`).
- `.github/workflows/ci.yml`: Added `uv run mkdocs build --strict` to continuous integration testing.
- `scripts/build_docs_structure.py`: Automated documentation generator script.
- `README.md` & `CONTRIBUTING.md`: Added documentation website badges, links, and local preview commands (`uv run mkdocs serve`).

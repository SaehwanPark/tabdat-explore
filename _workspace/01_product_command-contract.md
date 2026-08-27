# Product Contract: CI/CD Workflows, Packaging Baseline & Frictionless Shell Installer

## Request Summary
Establish continuous delivery automation, production packaging configuration, and one-command shell installation.

## Roadmap Phase
Phase 25 (Package & Installability Baseline), Phase 26 (Release Automation & CI), and Phase 27 (Frictionless Shell Installation).

## Specification & Behavioral Invariants

### 1. Packaging Metadata (`pyproject.toml`)
- Production package name: `tabdat-explore`
- CLI executable script: `tabdat = "tabdat.cli:main"`
- Python version requirement: `>=3.13`
- Included resources: `src/tabdat/help/topics/*.md` packaged in wheel and sdist distributions.
- Metadata: project URLs (Homepage, Repository, Issues, Documentation), authors, keywords, classifiers.

### 2. CI Workflow (`.github/workflows/ci.yml`)
- Triggered on: push to `main` and pull requests.
- Matrix: `ubuntu-latest`, `macos-latest` on Python `3.13`.
- Steps:
  1. Checkout code.
  2. Setup Python & `uv`.
  3. Run static checks (`ruff check`, `ruff format --check`, `basedpyright`).
  4. Run docs alignment (`scripts/check_docs_alignment.py`).
  5. Run pytest suite (`pytest`).
  6. Run integrated E2E suite (`integrated_testing/run_e2e.py`).
  7. Build wheel (`uv build`) and test clean installation in an isolated venv.

### 3. Release Workflow (`.github/workflows/release.yml`)
- Triggered on: push of tags matching `v*`.
- Builds wheel and source distributions.
- Runs verification against built wheel.
- Creates GitHub Release with release notes and attaches built distribution artifacts with SHA256 checksums.

### 4. Shell Installer (`scripts/install.sh`)
- Executable POSIX shell script:
  - Verifies operating system (Linux / macOS) and CPU architecture.
  - Checks if `uv` is available on PATH; if not, installs `uv` using official installer or provides direct instructions.
  - Installs TabDat globally via `uv tool install tabdat-explore` (or `--from git+https://github.com/SaehwanPark/tabdat-explore.git`).
  - Verifies installation with `tabdat doctor` and `tabdat --version`.
  - Prints friendly quickstart onboarding banner.

## Acceptance Criteria
- [ ] `pyproject.toml` contains complete package metadata and wheel build config.
- [ ] `.github/workflows/ci.yml` and `.github/workflows/release.yml` created with valid GitHub Actions syntax.
- [ ] `scripts/install.sh` created, executable, and passing syntax validation (`sh -n scripts/install.sh`).
- [ ] `tests/test_packaging_and_installer.py` validates wheel build and installer script syntax/behavior.
- [ ] All tests, type checks, and docs alignment checks pass.

# Request Summary: CI/CD Workflows, Packaging Baseline & Frictionless Shell Installer

## Goal
Implement the release, installation, and CI/CD foundations specified in Phases 25, 26, and 27 of `docs/tabdat_forward_roadmap.md`:
1. Production packaging metadata in `pyproject.toml` (package URLs, classifiers, wheel resource packaging).
2. Continuous Integration workflow `.github/workflows/ci.yml` verifying linting, formatting, type checking, docs alignment, test suite, and clean-wheel installation across Linux and macOS.
3. Tagged release automation workflow `.github/workflows/release.yml`.
4. Frictionless shell installer `scripts/install.sh` for one-command installation (`curl -LsSf ... | sh`) via `uv tool`.
5. Packaging and installer verification tests.

## Phase Fit
Phases 25, 26, and 27 (`docs/tabdat_forward_roadmap.md` Sections 8, 9, 10).

## Touched Surfaces
- `pyproject.toml`: Production package metadata and build settings.
- `.github/workflows/ci.yml`: GitHub Actions PR and branch validation workflow.
- `.github/workflows/release.yml`: Tagged GitHub Release and packaging workflow.
- `scripts/install.sh`: Shell installer script.
- `tests/test_packaging_and_installer.py`: Build and installer validation tests.
- Documentation: `README.md`, `CONTRIBUTING.md`, `docs/tabdat_forward_roadmap.md`.

## Assumptions
- Uses standard POSIX-compliant `/bin/sh` for `scripts/install.sh`.
- Wheel builds via standard `hatchling` backend / `uv build`.
- CI uses standard GitHub Actions runners (`ubuntu-latest`, `macos-latest`) with Astral `uv` setup action.

## Non-Goals
- Native C/Rust compiler toolchains.

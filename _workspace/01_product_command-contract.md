# Product Contract: Homebrew Formula & Packaging Architecture Decision Record

## Request Summary
Provide standard Homebrew formula packaging and record architectural decisions governing distribution channels, binary freezing trade-offs, and capability scoping.

## Roadmap Phase
Phases 28 & 29 (Homebrew Distribution & Standalone Packaging Evaluation).

## Specification & Validation Rules

### 1. Homebrew Formula (`Formula/tabdat.rb`)
- Implements standard Homebrew `Formula` subclass `Tabdat`.
- Requires Python 3.13 or `uv`.
- Configures virtualenv/isolated tool installation into Homebrew `libexec` and symlinks `bin/tabdat` into standard Homebrew `bin`.
- Includes `test` block executing `tabdat doctor` and `tabdat -c "describe"`.

### 2. Architecture Decision Record (`docs/adr/0001-distribution-and-packaging-strategy.md`)
- Conforms to standard MADR / ADR format: Title, Status, Context, Decision, Consequences, Evaluation Matrix.
- Evaluates:
  - `uv tool` / shell curl installer vs. Homebrew formula vs. PyInstaller `onedir`/`onefile` vs. Nuitka standalone.
  - Startup latency (cold/warm), package footprint, dependency graph weight, cross-platform portability.
  - Decision: Standardize on `uv tool` as primary engine under the shell curl installer and Homebrew formula; gate optional statistical ecosystems behind `doctor` diagnostics rather than giant bundled monoliths.

## Acceptance Criteria
- [ ] `Formula/tabdat.rb` exists, is syntactically valid Ruby, and defines valid installation and test methods.
- [ ] `docs/adr/0001-distribution-and-packaging-strategy.md` exists and satisfies all Phase 29 ADR evaluation criteria.
- [ ] `tests/test_homebrew_formula.py` passes.
- [ ] `scripts/check_docs_alignment.py` and `pytest` pass.

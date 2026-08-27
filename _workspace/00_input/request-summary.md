# Request Summary: Homebrew Formula & Distribution Architecture Decision Record

## Goal
Implement Phase 28 (Homebrew Distribution) and Phase 29 (Standalone Packaging Evaluation & ADR) of `docs/tabdat_forward_roadmap.md`:
1. Create standard Homebrew formula `Formula/tabdat.rb` enabling `brew install SaehwanPark/tabdat/tabdat` or custom tap installation.
2. Author ADR `docs/adr/0001-distribution-and-packaging-strategy.md` defining distribution tiering, startup and payload trade-offs, and capability scoping.
3. Add automated formula validation test in `tests/test_homebrew_formula.py`.
4. Update docs and roadmap status.

## Phase Fit
Phases 28, 29, 30, 31 (`docs/tabdat_forward_roadmap.md` Sections 11, 12, 13, 14).

## Touched Surfaces
- `Formula/tabdat.rb`: Homebrew Ruby formula definition.
- `docs/adr/0001-distribution-and-packaging-strategy.md`: Architecture Decision Record.
- `tests/test_homebrew_formula.py`: Formula structure and syntax validation test.
- `README.md`, `CONTRIBUTING.md`, `docs/tabdat_forward_roadmap.md`.

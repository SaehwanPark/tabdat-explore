# Request Summary: MathJax LaTeX Math Rendering Support

## 1. Goal
Support LaTeX math rendering for the TabDat-Explore GitHub Pages documentation site using MathJax. Ensure compatibility with Material for MkDocs instant loading and configure the recommended delimiters (`\( .. \)` for inline math and `\\[ .. \\]` for display math). Update all relevant documentation files with these delimiters and conventions, open a Pull Request, and autonomously merge into `main`.

## 2. Constraints & Assumptions
- Math rendering engine: MathJax (v3).
- Delimiter convention: `\( .. \)` for inline math, `\\[ .. \\]` for display math.
- No codebase edits to core CLI/execution engine.
- No package version bumping.
- PR opened and autonomously merged to `main`.

## 3. Touched Surfaces
- `mkdocs.yml`: Added `pymdownx.arithmatex` extension with `generic: true` and `extra_javascript` linking `javascripts/mathjax.js` and MathJax v3 CDN (`tex-mml-chtml.js`).
- `docs/javascripts/mathjax.js`: Client-side MathJax 3 configuration and `document$.subscribe` hook for dynamic instant navigation re-typesetting.
- `docs/reference-validation-matrix.md`: Migrated LaTeX math expressions from `$ ... $` to `\( ... \)`.
- `CONTRIBUTING.md` & `docs/contributing.md`: Added math delimiter formatting conventions (`\( .. \)` and `\\[ .. \\]`) to development guidelines.
- `_workspace/`: Orchestration and delivery records.

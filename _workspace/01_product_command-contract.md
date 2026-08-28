# Product Contract: MathJax LaTeX Math Documentation Support

## 1. Documentation Math Specification
- **Engine**: MathJax v3 (TeX to HTML/CommonHTML via `tex-mml-chtml.js`).
- **Markdown Extension**: `pymdownx.arithmatex` (`generic: true`).
- **Inline Delimiters**: `\( ... \)` rendering to `<span class="arithmatex">\( ... \)</span>` -> MathJax typeset inline element.
- **Display Delimiters**: `\\[ ... \\]` rendering to `<div class="arithmatex">\[ ... \]</div>` -> MathJax typeset block element.
- **Dynamic Navigation Hook**: `document$.subscribe` observer calls `MathJax.typesetPromise()` alongside cache/state reset (`MathJax.startup.output.clearCache()`, `MathJax.typesetClear()`, `MathJax.texReset()`) upon Material for MkDocs instant-page navigation.

## 2. Updated Document Delimiters
- `docs/reference-validation-matrix.md`:
  - Numerical tolerance expressions: `\(10^{-5}\)` to `\(10^{-6}\)`, `\(10^{-4}\)`.
  - Statistics notation: `\(R^2\)`, `\(q \in (0,1)\)`.
- `CONTRIBUTING.md` & `docs/contributing.md`:
  - Explicit contributor guideline specifying `\( .. \)` for inline math and `\\[ .. \\]` for display math.

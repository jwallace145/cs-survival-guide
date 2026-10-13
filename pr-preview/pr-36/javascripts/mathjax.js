// MathJax configuration for pymdownx.arithmatex in generic mode. Arithmatex
// wraps math in elements with the "arithmatex" class, delimited by \( \) and
// \[ \], and MathJax is told to typeset only those elements.
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

// With instant navigation, pages are swapped in without a full reload, so
// typeset again each time the document changes.
document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});

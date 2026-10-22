<!--
WRITING MATHS ON THIS PAGE

Maths is LaTeX, typeset by MathJax (pymdownx.arithmatex). Two forms:

  Inline, inside a sentence:   the sum is $\frac{n(n+1)}{2}$ copies.
  Display, on its own lines:

      $$
      \sum_{i=1}^{n} i = \frac{n(n+1)}{2}
      $$

Pieces you will use most:

  \sum_{i=1}^{n} i            a sum from i = 1 to n
  \sum_{i=0}^{m-1} 2^i        a sum from 0; braces group multi-character limits
  \frac{n^2}{2k}              a fraction
  2^{m-1}, n_0, c_0           superscripts and subscripts; braces when longer than one character
  \lfloor x \rfloor           floor; \lceil x \rceil is ceiling
  \le  \ge  \ne  \approx      comparisons
  \Theta(n)  O(1)  \Omega(n)  asymptotic notation (O is just a capital O)
  \cdot  \times  \dots        a dot product sign, a times sign, an ellipsis
  \;  \,  \quad               small, tiny and large horizontal spaces

A multi-line derivation lines up on the & and breaks on \\. The [4pt]
adds a little vertical space between the lines:

      $$
      \begin{aligned}
      C(n) &= \sum_{i=0}^{m-1} 2^i \\[4pt]
           &= 2^m - 1 \\[4pt]
           &< 2n
      \end{aligned}
      $$

Link a formula to the cheat sheet rather than re-deriving it:

      the [geometric series](../math/cheat-sheet.md#geometric-series)

Link the kit with a mkdocstrings cross-reference:

      [`DynamicArray`][cs_survival_kit.data_structures.dynamic_array.DynamicArray]

Optional detail goes in a collapsible admonition; indent its body by
four spaces, and the maths inside it needs the same indent:

      ??? note "Starting from any initial capacity"

          Body text here.

          $$
          m = \left\lceil \frac{n - c_0}{k} \right\rceil
          $$

Wrap prose at about 78 columns. British spelling, except the conventional
"amortized". Delete this comment block when the page is done.
-->

# Amortized Append

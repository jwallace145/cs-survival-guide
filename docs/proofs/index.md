# Proofs

The results that every data structures and algorithms course proves, and
that interviews keep asking about. Each page states one claim, proves it in
full, and is the single place the rest of the guide links to when it needs
the result: a structure page says *what* an operation costs and points here
for *why*.

The proofs lean on the formulas in the [math cheat sheet](../math/cheat-sheet.md).
When a derivation needs a formula that is not there yet, it is added to the
cheat sheet with its own anchor, so the proof stays about the idea.

## The proofs

| Claim | Used by | Proof |
| --- | --- | --- |
| Appending to a dynamic array costs $O(1)$ amortized under geometric growth, and $\Theta(n)$ under additive growth | [Dynamic array](../data-structures/dynamic-array.md), [stack](../data-structures/stack.md), [queue](../data-structures/queue.md) | [Amortized append](dynamic-array-amortized-append.md) |

<!--
Add one row per proof, in the order the pages read best. The "Used by"
column lists the guide pages that quote the result; keep it in step with
the links on those pages so a reader can go both ways.
-->

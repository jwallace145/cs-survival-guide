# Math Cheat Sheet

Quick-reference formulas that come up again and again when analysing
algorithms by hand. Each entry gives the formula, where it tends to appear,
and a small example.

## At a glance

| Name | Formula | Growth |
| --- | --- | --- |
| [Arithmetic series](#arithmetic-series) | $\displaystyle\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$ | $\Theta(n^2)$ |
| [Sum of squares](#sum-of-squares) | $\displaystyle\sum_{i=1}^{n} i^2 = \frac{n(n+1)(2n+1)}{6}$ | $\Theta(n^3)$ |
| [Sum of cubes](#sum-of-cubes) | $\displaystyle\sum_{i=1}^{n} i^3 = \left(\frac{n(n+1)}{2}\right)^2$ | $\Theta(n^4)$ |
| [Geometric series](#geometric-series) | $\displaystyle\sum_{i=0}^{n} r^i = \frac{r^{n+1} - 1}{r - 1}$ | $\Theta(r^n)$ for $r > 1$ |
| [Powers of two](#geometric-series) | $\displaystyle\sum_{i=0}^{n} 2^i = 2^{n+1} - 1$ | $\Theta(2^n)$ |

## Summation rules

These three rules are what let you reduce an unfamiliar sum to one of the
formulas on this page.

**Pull out a constant factor.** Anything that does not depend on the index
can move outside the sum:

$$
\sum_{i=1}^{n} c \cdot f(i) = c \sum_{i=1}^{n} f(i)
$$

**Split a sum of terms.** A sum of a sum is the sum of the sums:

$$
\sum_{i=1}^{n} \bigl( f(i) + g(i) \bigr) = \sum_{i=1}^{n} f(i) + \sum_{i=1}^{n} g(i)
$$

**Sum a constant.** Adding the same value $n$ times:

$$
\sum_{i=1}^{n} c = c \cdot n
$$

!!! example

    $$
    \sum_{i=1}^{n} (3i + 2)
      = 3 \sum_{i=1}^{n} i + \sum_{i=1}^{n} 2
      = \frac{3n(n+1)}{2} + 2n
    $$

## Arithmetic series

The sum of the first $n$ positive integers:

$$
\sum_{i=1}^{n} i = 1 + 2 + 3 + \dots + n = \frac{n(n+1)}{2}
$$

More generally, any sequence that rises by a fixed difference $d$ sums to
the number of terms times the average of the first and last term:

$$
\sum_{i=1}^{n} a_i = \frac{n \, (a_1 + a_n)}{2}
\qquad \text{where } a_i = a_1 + (i - 1)\,d
$$

**Where it shows up:** nested loops where the inner loop runs $i$ times
(insertion sort, bubble sort, comparing every pair), and any process whose
cost per step grows by a fixed amount, such as a
[dynamic array with additive growth](../data-structures/dynamic-array.md#counting-the-copies-additive-growth).

!!! example

    $1 + 2 + \dots + 100 = \dfrac{100 \cdot 101}{2} = 5050$

## Sum of squares

$$
\sum_{i=1}^{n} i^2 = 1^2 + 2^2 + 3^2 + \dots + n^2 = \frac{n(n+1)(2n+1)}{6}
$$

**Where it shows up:** triple-nested loops, and loops whose body costs
$\Theta(i^2)$ on the $i$-th iteration.

!!! example

    $1^2 + 2^2 + 3^2 + 4^2 = \dfrac{4 \cdot 5 \cdot 9}{6} = 30$

## Sum of cubes

$$
\sum_{i=1}^{n} i^3 = 1^3 + 2^3 + 3^3 + \dots + n^3 = \left( \frac{n(n+1)}{2} \right)^2
$$

The sum of the first $n$ cubes is the square of the sum of the first $n$
integers.

!!! example

    $1^3 + 2^3 + 3^3 + 4^3 = \left( \dfrac{4 \cdot 5}{2} \right)^2 = 10^2 = 100$

!!! tip "The pattern"

    Summing a power raises the exponent by one. For any fixed $p \ge 0$:

    $$
    \sum_{i=1}^{n} i^p = \Theta\!\left(n^{p+1}\right)
    $$

    with leading term $\dfrac{n^{p+1}}{p+1}$. That is often all a
    complexity analysis needs.

## Sums that start at index 0

The formulas above start at $i = 1$, but loops usually start at $0$. There
are two ways to bridge the gap.

**Peel off the $i = 0$ term.** Take the first term out and the rest of the
sum starts at 1:

$$
\sum_{i=0}^{n} f(i) = f(0) + \sum_{i=1}^{n} f(i)
$$

For powers of $i$ the peeled term is zero, so the sum is unchanged:

$$
\sum_{i=0}^{n} i = 0 + \sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

**Watch the upper limit.** A loop `for i in range(n)` runs $i$ from $0$ to
$n - 1$, not to $n$. Substitute $n - 1$ for $n$ in the formula:

$$
\sum_{i=0}^{n-1} i = \frac{(n-1)\,n}{2}
$$

**Shift the index.** Substituting $j = i + 1$ moves the whole range up by
one. The limits go up by one and every $i$ inside becomes $j - 1$:

$$
\sum_{i=0}^{n-1} f(i) = \sum_{j=1}^{n} f(j - 1)
$$

!!! example

    A sum with a non-zero first term, starting from 0:

    $$
    \begin{aligned}
    \sum_{i=0}^{n-1} (c + ik)
      &= \sum_{i=0}^{n-1} c + k \sum_{i=0}^{n-1} i \\
      &= cn + k \cdot \frac{(n-1)\,n}{2}
    \end{aligned}
    $$

**Sums that start anywhere.** A sum from $a$ to $b$ has $b - a + 1$ terms,
and is the difference of two sums that start at 1:

$$
\sum_{i=a}^{b} f(i) = \sum_{i=1}^{b} f(i) - \sum_{i=1}^{a-1} f(i)
$$

## Geometric series

Each term is the previous one times a fixed ratio $r \ne 1$:

$$
\sum_{i=0}^{n} r^i = 1 + r + r^2 + \dots + r^n = \frac{r^{n+1} - 1}{r - 1}
$$

The case that matters most is $r = 2$:

$$
\sum_{i=0}^{n} 2^i = 1 + 2 + 4 + \dots + 2^n = 2^{n+1} - 1
$$

In words: a sum of doubling terms is just under twice its last term. When
$r > 1$, the last term dominates and the whole sum is $\Theta(r^n)$.

When $|r| < 1$ the terms shrink, and even the infinite sum is finite:

$$
\sum_{i=0}^{\infty} r^i = \frac{1}{1 - r}
\qquad \text{so} \qquad
\sum_{i=0}^{\infty} \frac{1}{2^i} = 1 + \frac{1}{2} + \frac{1}{4} + \dots = 2
$$

**Where it shows up:** anything that doubles or halves. Resizing a
[dynamic array by doubling](../data-structures/dynamic-array.md#counting-the-copies-doubling),
the number of nodes in a complete binary tree, and the total work of
algorithms that halve their input at each step.

!!! example

    A complete binary tree with levels $0$ to $h$ has
    $1 + 2 + 4 + \dots + 2^h = 2^{h+1} - 1$ nodes.

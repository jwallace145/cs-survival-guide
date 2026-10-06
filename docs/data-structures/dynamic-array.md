---
render_macros: true
---

# Dynamic Array

A dynamic array is an array that grows. It stores its elements in a
fixed-size block of memory and, when that block fills up, allocates a larger
one and copies everything across. Python's `list`, Java's `ArrayList` and
C++'s `std::vector` are all dynamic arrays.

The guide's implementation is
[`DynamicArray`][cs_survival_kit.data_structures.dynamic_array.DynamicArray].
For the other classic way to store a sequence, and how the two compare, see
the [singly linked list](singly-linked-list.md) and the
[doubly linked list](doubly-linked-list.md).

## How it works

The array keeps two numbers: its **length**, the number of elements in use,
and its **capacity**, the number of slots allocated. Appending writes into
the next free slot. When the length reaches the capacity there is no free
slot, so the array **resizes**: it allocates a new block, copies every
element into it, and carries on.

A single resize costs O(n), because it copies all n elements. What matters is
how often that happens, and that is decided by the **growth policy**: the
rule for choosing the new capacity.

## Growth policies

| Policy | New capacity | In the library |
| --- | --- | --- |
| Doubling | twice the current capacity | [`doubling`][cs_survival_kit.data_structures.dynamic_array.doubling] |
| Geometric | the current capacity times a factor above 1 | [`geometric`][cs_survival_kit.data_structures.dynamic_array.geometric] |
| Additive | the current capacity plus a fixed step | [`additive`][cs_survival_kit.data_structures.dynamic_array.additive] |

Doubling is geometric growth with a factor of 2.

## Amortized cost of append

With **geometric** growth, each resize is bigger than the last, but resizes
also become rarer at exactly the same rate. Appending n elements copies
fewer than 2n elements in total with doubling, so the average cost per append
is constant. This is **amortized O(1)**: an individual append is occasionally
expensive, but any long run of appends averages out to a constant each.

With **additive** growth, resizes never become rarer. A step of 16 copies the
whole array every 16 appends, forever, which adds up to about n² / 32 copies
for n appends. Each append costs O(n) on average.

The two subsections below count the copies exactly. The formulas they lean
on are collected in the [math cheat sheet](../math/cheat-sheet.md).

### Counting the copies: additive growth

Take an array that grows by a fixed step of $k$ slots and, to keep the
arithmetic clean, starts with a capacity of $k$. Append $n$ elements and
count every element copied by a resize.

**When do resizes happen?** The capacity is always a multiple of $k$, and a
resize happens when an append finds the array full. So the resizes happen at
lengths

$$
k, \; 2k, \; 3k, \; \dots, \; mk
$$

where $m$ is the number of resizes. The last one happens at the largest
multiple of $k$ that is still below $n$, so

$$
m = \left\lfloor \frac{n - 1}{k} \right\rfloor
$$

**What does each resize cost?** A resize copies every element in the array.
The $i$-th resize happens at length $ik$, so it copies $ik$ elements.

**Add them up.** The total number of copies $C(n)$ is the sum over all $m$
resizes. The step $k$ is a constant, so it factors out, and what is left is
the [arithmetic series](../math/cheat-sheet.md#arithmetic-series):

$$
\begin{aligned}
C(n) &= \sum_{i=1}^{m} ik \\[4pt]
     &= k \sum_{i=1}^{m} i \\[4pt]
     &= k \cdot \frac{m(m+1)}{2}
\end{aligned}
$$

**Put it in terms of $n$.** The number of resizes $m$ is $n / k$, give or
take rounding. Substituting $m \approx n / k$:

$$
\begin{aligned}
C(n) &\approx \frac{k}{2} \cdot \frac{n}{k} \left( \frac{n}{k} + 1 \right) \\[4pt]
     &= \frac{n^2}{2k} + \frac{n}{2}
\end{aligned}
$$

Handling the rounding exactly moves the answer by at most $n$. For every
$n \ge k$:

$$
\frac{n^2}{2k} - \frac{n}{2} \;\le\; C(n) \;\le\; \frac{n^2}{2k} + \frac{n}{2}
$$

The $n^2$ term dominates both bounds, so

$$
C(n) = \Theta(n^2)
$$

The number of copies grows **quadratically** with the number of appends:
doubling $n$ quadruples the copying. With a step of $k = 16$ the leading
term is $n^2 / 32$, the figure quoted above.

**Amortize.** The amortized cost of one append is the total cost of $n$
appends divided by $n$. Each append also does one write of its own, which
adds $n$ to the total:

$$
\frac{C(n) + n}{n} \approx \frac{n}{2k} + \frac{3}{2} = \Theta(n)
$$

Each append costs **linear** time on average. The step $k$ only appears in
the denominator of a constant: a larger step makes the line shallower, but
it is still a line.

??? note "Starting from any initial capacity"

    If the array starts with a capacity of $c_0$ instead of $k$, the
    resizes happen at lengths $c_0, \; c_0 + k, \; c_0 + 2k, \; \dots$ and
    there are $m = \lceil (n - c_0) / k \rceil$ of them. Numbering them from
    0, the sum
    [starts at index 0](../math/cheat-sheet.md#sums-that-start-at-index-0):

    $$
    \begin{aligned}
    C(n) &= \sum_{i=0}^{m-1} (c_0 + ik) \\[4pt]
         &= \sum_{i=0}^{m-1} c_0 + k \sum_{i=0}^{m-1} i \\[4pt]
         &= m \, c_0 + k \cdot \frac{(m-1)\,m}{2}
    \end{aligned}
    $$

    With $m \approx n / k$ the leading term is still $n^2 / (2k)$. The
    initial capacity changes only the lower-order terms.

### Counting the copies: doubling

Run the same count for an array that starts with a capacity of 1 and
doubles. Now the resizes happen at lengths

$$
1, \; 2, \; 4, \; \dots, \; 2^{m-1}
$$

and the last of them is below $n$, so $2^{m-1} < n$. The total is a
[geometric series](../math/cheat-sheet.md#geometric-series):

$$
\begin{aligned}
C(n) &= \sum_{i=0}^{m-1} 2^i \\[4pt]
     &= 2^m - 1 \\[4pt]
     &< 2n
\end{aligned}
$$

Fewer than $2n$ copies for $n$ appends, so $C(n) = \Theta(n)$ and the
amortized cost of an append is

$$
\frac{C(n) + n}{n} < 3 = \Theta(1)
$$

The difference between the two policies is the difference between the two
series. An arithmetic series sums to roughly the *square* of its number of
terms, and additive growth has $n / k$ terms. A geometric series sums to
roughly twice its *last* term, and the last term here is below $n$.

### Measured

The benchmark below appends n integers to an empty array and times the whole
run. The first tab divides each time by n, giving the cost of one append: a
line that stays flat is constant cost per append, and one that climbs is not.
The second tab shows the total time, where the steeper line is the quadratic
one. Both axes are logarithmic.

{{ benchmark("dynamic_array.append") }}

Both geometric policies stay flat as n grows by four orders of magnitude,
just like the built-in `list`. The additive column grows in step with n.
`list` is faster throughout because it is implemented in C; what the two
share is the shape of the curve.

## Choosing a factor

Any factor above 1 gives amortized O(1) appends. The factor trades time for
memory: a larger one resizes less often, but leaves more of the capacity
unused straight after a resize.

{{ benchmark("dynamic_array.append.geometric_factors") }}

## A larger step does not fix additive growth

It is tempting to think a big enough step makes additive growth acceptable.
A larger step does start out cheap, but the cost per append still rises with
n. It delays the quadratic behaviour without removing it.

{{ benchmark("dynamic_array.append.additive_steps") }}

## Complexity

| Operation | Time | Notes |
| --- | --- | --- |
| Read or write by index | O(1) | |
| Append | O(1) amortized | O(n) for the append that triggers a resize |
| Pop from the end | O(1) | |
| Iterate | O(n) | |

These assume a geometric growth policy.

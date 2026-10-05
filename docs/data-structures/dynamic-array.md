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
the [singly linked list](singly-linked-list.md).

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

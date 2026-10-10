# CS Survival Guide

A field guide to computer science fundamentals — algorithms, data structures,
system design, distributed systems, databases, networking, operating systems,
concurrency, and AI.

The guide is treated as a **versioned software artifact**: every change lands
through a Conventional Commit, releases follow [Semantic
Versioning](https://semver.org), and the [changelog](changelog.md) records how
the guide grows over time.

## Topics

Content is organized into topic areas that grow release by release:

- **Algorithms & Data Structures** — patterns, complexity, and the classics
- **System Design & Distributed Systems** — building and scaling real systems
- **Databases** — storage engines, transactions, and query execution
- **Networking** — from the TCP handshake up through HTTP
- **Operating Systems & Concurrency** — processes, memory, and parallelism
- **AI** — modern machine learning fundamentals

See the [changelog](changelog.md) for what's new in each release.

## The library

The code behind the guide is
[cs-survival-kit](https://pypi.org/project/cs-survival-kit/), a Python
package of hand-written data structures and algorithms plus a small
benchmarking toolkit, developed in the open at
[jwallace145/cs-survival-kit](https://github.com/jwallace145/cs-survival-kit).
The guide explains the ideas; the kit is the code. The Reference section of
this site is rendered from the kit's docstrings, and every entry there links to
its source on GitHub, so a page, its API and its implementation can be read
side by side.

To use the implementations yourself:

```bash
pip install cs-survival-kit
```

Requires Python 3.12 or newer. The core package has no runtime dependencies.

```python
from cs_survival_kit.data_structures import DynamicArray

numbers = DynamicArray[int]()            # doubles its capacity when full
numbers.append(1)
numbers.append(2)
numbers.pop_back()                       # 2
len(numbers), numbers.capacity           # (1, 4)
```

Issues and pull requests on the kit are welcome: a clearer implementation, a
sharper docstring or a benchmark that exposes a surprising curve all make the
guide better too.

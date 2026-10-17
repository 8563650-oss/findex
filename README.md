# Findex - Search Engine (Lab 3)

This repository contains the third iteration of the `findex` search engine. In this phase, we transitioned the inverted index to a robust Object-Oriented model using Python's Data Model (dunder methods), implemented ranking algorithms (TF-IDF and BM25), built an AST-based query parser, and applied decorators for caching and profiling.

## Decorators & Context Managers
We implemented a custom `@timed` decorator using `functools.wraps` to profile execution time, and used `@lru_cache` to cache search results. The index lifecycle is managed via a `with open_index()` context manager to ensure safe resource allocation and teardown. 

**Execution Logs:**
```text
=== Building Index ===
[build] executed in 2.2187 seconds.
[save] executed in 0.0665 seconds.
<Index: 1000 70 docs terms,>

=== Sanity Checks (BM25) ===
Opening index from index.bin...
[load] executed in 0.0663 seconds.

--- Cache Test ---
First call:
[search] executed in 0.0018 seconds.
Second call (should be instant due to cache):
[search] executed in 0.0000 seconds.
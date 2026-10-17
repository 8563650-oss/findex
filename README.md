# Findex - Search Engine (Lab 2)

This repository contains the second iteration of the `findex` search engine. In this lab, we implemented an inverted index, explored efficient memory management in Python (`__slots__`, `array`), and implemented Boolean AND search.

## Memory Profiling: Storing Postings
We compared three different ways to store posting lists (document ID and frequency) in memory for our 50 MB synthetic corpus.

| Data Structure | Peak Memory (MB) |
|----------------|------------------|
| Normal Dataclass | 754.87 MB        |
| Dataclass with `slots=True` | 442.55 MB |
| Python `array('I')` | 65.70 MB |

### Reflection: Where did the bytes go?
In Python, standard objects (like a normal `@dataclass`) maintain a dynamic `__dict__` to store attributes, which adds significant memory overhead (often over 100 bytes per object). By using `@dataclass(slots=True)`, we tell Python to allocate a fixed amount of space for the explicitly declared fields (`doc_id`, `frequency`), removing the `__dict__` dictionary overhead. This reduced memory usage by ~40% (from 755 MB to 442 MB). 

However, storing millions of individual Python objects is still inefficient. The `array('I')` approach drastically cuts memory down to `65.70 MB` because it stores raw C-style unsigned integers consecutively in a single block of memory, completely eliminating the Python object wrapper overhead for each posting.

## Serialization (Index Saving/Loading)
We serialized the built index into two formats to compare speed and size.

| Format | Save Time (s) | File Size (MB) |
|--------|---------------|----------------|
| Pickle | 0.063 s       | 1.04 MB        |
| JSON   | 0.130 s       | 1.43 MB        |

**Security Note on Pickle:** 
While `pickle` is twice as fast and produces a slightly smaller file, loading a `.pkl` file from an untrusted source is extremely dangerous. Pickle allows for arbitrary code execution during the unpickling process (e.g., via the `__reduce__` method). An attacker could craft a malicious pickle file that runs a reverse shell or deletes files on the host machine. JSON is a secure, plain-text alternative.

## Boolean Search Benchmark (AND)
Query: `stream AND parameters` (Found 1,000 matching documents)

| Algorithm | Total Time (Load + Search) | Peak Memory |
|-----------|----------------------------|-------------|
| Two-Pointer Merge | 0.3151 s | 16.72 MB |
| Python `set` Intersection | 0.3216 s | 16.72 MB |
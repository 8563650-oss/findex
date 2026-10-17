# Findex - Search Engine (Lab 1)

This repository contains the first iteration of the `findex` search engine, focusing on lazy evaluation, iterators, generators, and memory profiling.

## Text Corpus
The corpus consists of 1,000 synthetic technical documents (logs, AI model parameters, and terminal outputs) totaling exactly 50 MB of `.txt` files.

## Performance & Memory Profiling

We compared two text processing pipelines:
1. **Lazy Pipeline (Generators):** Reads files one by one and yields tokens dynamically.
2. **Greedy Pipeline (Lists):** Loads all documents into memory and creates a single massive list of all tokens before counting.

| Approach | Peak Memory (MB) | Execution Time (s) | Document Count | Total Tokens |
|----------|------------------|--------------------|----------------|--------------|
| Lazy     | 0.42 MB          | 13.74 s            | 1,000          | 8,187,161    |
| Greedy   | 518.56 MB        | 10.17 s            | 1,000          | 8,187,161    |

### Top 5 Terms
1. threshold (307,972)
2. connection (307,946)
3. parameters (307,831)
4. stream (307,791)
5. process (300,000)

### Reflection / Memory Explanation
**Where did the memory go in the greedy approach?**
In the lazy approach, memory is only used to store one document and its active variables at a time, keeping peak memory extremely low (`0.42 MB`). 

In the greedy approach, the memory footprint exploded to `518.56 MB`. This happens because we store `all_docs` (a list containing all raw text strings, ~50 MB) and `all_tokens` (a list containing over 8 million tokenized string objects). In Python, every string object has a significant memory overhead. A list of 8 million short strings consumes vastly more memory than the raw 50 MB text files combined.
## Lab 6: Asyncio Crawler

This iteration introduces a high-performance, asynchronous web crawler built with `asyncio` and `httpx`. The crawler supports concurrent HTTP requests, respects `robots.txt` (with caching per host), implements exponential backoff with jitter for 429/5xx responses, and parses HTML streams out to JSONL to limit memory consumption.

### Benchmark Results (Target: `https://docs.python.org/3/`, 200 pages)

| Concurrency | Wall Time | Pages/sec | Errors | Peak RSS (MB) |
|-------------|-----------|-----------|--------|---------------|
| 1           | ~260 s    | 0.77      | 10     | ~ 30 MB       |
| 5           | ~185 s    | 1.08      | 0      | ~ 35 MB       |
| 20          | ~178 s    | 1.12      | 10     | ~ 40 MB       |

### Reflection
* **Why 20 concurrent requests in 1 thread is faster than multiprocessing (Lab 5):** Web crawling is heavily I/O-bound. The CPU spends most of its time waiting for network packets. `asyncio`'s event loop multiplexes these wait times over a single thread, completely avoiding the heavy overhead of OS process creation and IPC context switching.
* **Why the per-host rate limit is kept (and its cost):** The per-host limit (`asyncio.Lock` + 0.5s sleep) prevents our crawler from accidentally DDoS-ing a target server or triggering 429 Too Many Requests bans. The cost of this limit is visible in our benchmark: when crawling a single domain, a concurrency of 20 is barely faster than 5, because all workers are bottlenecked by the same host lock.
* **Blocking the Event Loop:** If we ran our heavy CPU-bound indexing process (`findex index`) inside the asyncio coroutine without delegating it to an executor, the entire event loop would block. No new HTTP requests would be sent, timeouts would trigger, and the queue would stall.
* **Error handling log snippet:**
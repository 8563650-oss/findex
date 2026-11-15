import time
from findex.indexer import Index
from findex.ranking import BM25Scorer
from findex.searcher import RankedSearcher

idx = Index()
idx.load("index.bin")
scorer = BM25Scorer()
searcher = RankedSearcher(idx, scorer)

queries = ["python", "rare", "python AND stream AND search"]

print("| Запит / Термін | Час виконання (мс) |")
print("|----------------|-------------------|")
for q in queries:
    start = time.perf_counter()
    for _ in range(100):
        searcher.search(q, top_k=10)
    elapsed = ((time.perf_counter() - start) / 100) * 1000  # переводимо в мілісекунди за 1 запит
    print(f"| {q} | {elapsed:.4f} мс |")
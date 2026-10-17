import tracemalloc
import time
import os
import array
from collections import defaultdict
from dataclasses import dataclass
from findex.indexer import InvertedIndex

@dataclass
class NormalPosting:
    doc_id: int
    frequency: int

@dataclass(slots=True)
class SlotsPosting:
    doc_id: int
    frequency: int

def profile_postings(corpus_path="data"):
    
    from findex.core import iter_documents, tokenize
    
    print("Профілювання використання пам'яті...")
    methods = {
        "Normal Dataclass": lambda d, f: NormalPosting(d, f),
        "Slots=True Dataclass": lambda d, f: SlotsPosting(d, f),
    }

    for name, factory in methods.items():
        tracemalloc.start()
        idx = defaultdict(list)
        for doc_id, text in enumerate(iter_documents(corpus_path)):
            for token in tokenize(text):
                idx[token].append(factory(doc_id, 1))
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"{name}: {peak / 1024 / 1024:.2f} MB")

    
    tracemalloc.start()
    idx_arr = defaultdict(lambda: array.array('I'))
    for doc_id, text in enumerate(iter_documents(corpus_path)):
        for token in tokenize(text):
            idx_arr[token].append(doc_id)
            idx_arr[token].append(1) # частота
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Python array('I'): {peak / 1024 / 1024:.2f} MB\n")

if __name__ == "__main__":
    profile_postings()
    
    print("Вимірювання розміру файлів індексу...")
    idx = InvertedIndex()
    idx.build("data")
    
    t0 = time.time()
    idx.save_pickle("index.bin")
    t1 = time.time()
    print(f"Pickle save: {t1-t0:.3f}s, Size: {os.path.getsize('index.bin') / 1024 / 1024:.2f} MB")
    
    t0 = time.time()
    idx.save_json("index.json")
    t1 = time.time()
    print(f"JSON save: {t1-t0:.3f}s, Size: {os.path.getsize('index.json') / 1024 / 1024:.2f} MB")
import argparse
import tracemalloc
import time
from findex.indexer import InvertedIndex
from findex.searcher import BooleanSearch

def main():
    parser = argparse.ArgumentParser(description="Search in Inverted Index")
    parser.add_argument("index_file", help="Path to saved index.bin")
    parser.add_argument("query", help="Two terms for AND search (e.g. 'yolov8 ubuntu')")
    parser.add_argument("--engine", choices=["merge", "set"], default="merge", help="Search engine algorithm")
    args = parser.parse_args()

    terms = args.query.lower().split()
    if len(terms) != 2:
        print("Please provide exactly two terms for Boolean AND search in this demo.")
        return

    tracemalloc.start()
    start = time.time()

    idx = InvertedIndex()
    idx.load_pickle(args.index_file)
    searcher = BooleanSearch(idx)

    if args.engine == "merge":
        res = searcher.search_and_merge(terms[0], terms[1])
    else:
        res = searcher.search_and_set(terms[0], terms[1])

    elapsed = time.time() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Query: '{terms[0]} AND {terms[1]}' | Engine: {args.engine}")
    print(f"Found {len(res)} matching documents.")
    print(f"Time (Load + Search): {elapsed:.4f}s | Peak Memory: {peak / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()
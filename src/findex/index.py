import argparse
import tracemalloc
import time
from findex.indexer import InvertedIndex

def main():
    parser = argparse.ArgumentParser(description="Build Inverted Index")
    parser.add_argument("corpus", help="Path to corpus directory")
    parser.add_argument("--out", default="index.bin", help="Output index file")
    args = parser.parse_args()

    tracemalloc.start()
    start = time.time()

    idx = InvertedIndex()
    idx.build(args.corpus)
    idx.save_pickle(args.out)

    elapsed = time.time() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Index built and saved to {args.out}")
    print(f"Time: {elapsed:.3f}s | Peak Memory: {peak / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()
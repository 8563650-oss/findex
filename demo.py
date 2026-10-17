from findex.indexer import Index, open_index
from findex.ranking import TfIdfScorer, BM25Scorer
from findex.searcher import RankedSearcher
from findex.core import generate_snippet
from pathlib import Path

def main():
    print("=== Building Index ===")
    idx = Index()
    idx.build("data")
    idx.save("index.bin")
    print(idx)
    
    print("\n=== Sanity Checks (BM25) ===")
    with open_index("index.bin") as loaded_idx:
        bm25 = BM25Scorer()
        searcher = RankedSearcher(loaded_idx, bm25)
        
        print("\n--- Cache Test ---")
        print("First call:")
        searcher.search("yolov8 and stream")
        print("Second call (should be instant due to cache):")
        res = searcher.search("yolov8 and stream") # @timed не спрацює для кешу
        
        print("\n--- Top Results for 'yolov8 AND stream' ---")
        for i, hit in enumerate(res[:3]):
            meta = loaded_idx.get_meta(hit.doc_id)
            # Читаємо оригінальний файл для сніпету
            filepath = Path("data") / meta.name
            if filepath.exists():
                 text = filepath.read_text(encoding="utf-8")
                 snippet = generate_snippet(text, {"yolov8", "stream"}, window=40)
            else:
                 snippet = "File not found"
                 
            print(f"{i+1}. Doc {hit.doc_id} (Score: {hit.score:.4f})")
            print(f"   Snippet: {snippet}")

if __name__ == "__main__":
    main()
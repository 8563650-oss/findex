import tracemalloc
import time
from collections import Counter
from pathlib import Path
from findex.core import iter_documents, tokenize

def measure_lazy(corpus_path: str):
    tracemalloc.start()
    start_time = time.time()
    
    doc_count = 0
    token_count = 0
    vocab = Counter()
    
    # Лінивий конвеєр: документ -> токени -> підрахунок
    for doc in iter_documents(corpus_path):
        doc_count += 1
        for token in tokenize(doc):
            token_count += 1
            vocab[token] += 1
            
    elapsed_time = time.time() - start_time
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return doc_count, token_count, len(vocab), vocab.most_common(5), elapsed_time, peak_memory

def measure_greedy(corpus_path: str):
    tracemalloc.start()
    start_time = time.time()
    

    all_docs = []
    for file_path in Path(corpus_path).rglob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            all_docs.append(f.read())
            
    doc_count = len(all_docs)
    
    all_tokens = []
    for doc in all_docs:
        all_tokens.extend(list(tokenize(doc)))
        
    token_count = len(all_tokens)
    vocab = Counter(all_tokens)
    
    elapsed_time = time.time() - start_time
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return doc_count, token_count, len(vocab), vocab.most_common(5), elapsed_time, peak_memory

if __name__ == "__main__":
    corpus_dir = "data"  # Покладіть ваші .txt файли у папку data/
    
    print("=== Lazy Execution (Generators) ===")
    l_docs, l_tokens, l_vocab, l_top, l_time, l_mem = measure_lazy(corpus_dir)
    print(f"Docs: {l_docs}, Tokens: {l_tokens}, Vocab: {l_vocab}")
    print(f"Top 5: {l_top}")
    print(f"Time: {l_time:.4f}s, Peak Memory: {l_mem / 1024 / 1024:.2f} MB\n")
    
    print("=== Greedy Execution (Lists) ===")
    g_docs, g_tokens, g_vocab, g_top, g_time, g_mem = measure_greedy(corpus_dir)
    print(f"Time: {g_time:.4f}s, Peak Memory: {g_mem / 1024 / 1024:.2f} MB")
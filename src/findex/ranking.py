import math
import numpy as np
from typing import Protocol
from findex.indexer import Index

class Scorer(Protocol):
    """Протокол для моделей ранжування (Duck Typing)."""
    def score_array(self, index: Index, term: str) -> tuple[np.ndarray, np.ndarray]:
        ...

class TfIdfScorer:
    def score_array(self, index: Index, term: str) -> tuple[np.ndarray, np.ndarray]:
        doc_ids, freqs = index[term]
        if doc_ids.size == 0:
            return np.array([], dtype=np.int32), np.array([], dtype=np.float32)
            
        df = len(doc_ids)
        if df == 0:
            return doc_ids, np.zeros_like(doc_ids, dtype=np.float32)
            
        idf = math.log10(index.num_docs / df) if df > 0 else 0.0
        tf = freqs.astype(np.float32)
        scores = tf * idf
        return doc_ids, scores

class BM25Scorer:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score_array(self, index: Index, term: str) -> tuple[np.ndarray, np.ndarray]:
        doc_ids, freqs = index[term]
        if doc_ids.size == 0:
            return np.array([], dtype=np.int32), np.array([], dtype=np.float32)
            
        df = len(doc_ids)
        if df == 0:
            return doc_ids, np.zeros_like(doc_ids, dtype=np.float32)
            
        idf = math.log(1.0 + (index.num_docs - df + 0.5) / (df + 0.5))
        
        doc_lens = index._doc_lengths[doc_ids].astype(np.float32)
        avg_dl = index.avg_doc_length
        
        tf = freqs.astype(np.float32)
        numerator = tf * (self.k1 + 1.0)
        denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_lens / avg_dl))
        
        scores = idf * (numerator / denominator)
        return doc_ids, scores
import math
from typing import Protocol
from findex.indexer import Index
from findex.models import Posting

class Scorer(Protocol):
    """Протокол для моделей ранжування (Duck Typing)."""
    def score(self, index: Index, term: str, posting: Posting) -> float:
        ...

class TfIdfScorer:
    def score(self, index: Index, term: str, posting: Posting) -> float:
        tf = posting.frequency
        df = index.document_frequency(term)
        if df == 0: return 0.0
        
        idf = math.log10(index.num_docs / df)
        return tf * idf

class BM25Scorer:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, index: Index, term: str, posting: Posting) -> float:
        df = index.document_frequency(term)
        if df == 0: return 0.0
        
        idf = math.log(1 + (index.num_docs - df + 0.5) / (df + 0.5))
        
        doc_meta = index.get_meta(posting.doc_id)
        doc_len = doc_meta.length
        avg_dl = index.avg_doc_length
        
        tf = posting.frequency
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / avg_dl))
        
        return idf * (numerator / denominator)
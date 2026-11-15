import heapq
import numpy as np
from dataclasses import dataclass, field
from functools import lru_cache
from findex.indexer import Index
from findex.ranking import Scorer
from findex.core import timed

@dataclass(order=True)
class SearchResult:
    score: float
    doc_id: int = field(compare=False)

class QueryNode:
    def evaluate(self, index: Index) -> set[int]:
        raise NotImplementedError

class Term(QueryNode):
    def __init__(self, term: str):
        self.term = term
    def evaluate(self, index: Index) -> set[int]:
        doc_ids, _ = index[self.term]
        return set(doc_ids.tolist())

class And(QueryNode):
    def __init__(self, left: QueryNode, right: QueryNode):
        self.left = left
        self.right = right
    def evaluate(self, index: Index) -> set[int]:
        return self.left.evaluate(index) & self.right.evaluate(index)

class Or(QueryNode):
    def __init__(self, left: QueryNode, right: QueryNode):
        self.left = left
        self.right = right
    def evaluate(self, index: Index) -> set[int]:
        return self.left.evaluate(index) | self.right.evaluate(index)

class RankedSearcher:
    def __init__(self, index: Index, scorer: Scorer):
        self.index = index
        self.scorer = scorer

    @timed
    @lru_cache(maxsize=128)
    def search(self, query_string: str, top_k: int = 10) -> list[SearchResult]:
        parts = query_string.lower().split()
        if len(parts) == 3 and parts[1] == "and":
            tree = And(Term(parts[0]), Term(parts[2]))
            terms = [parts[0], parts[2]]
        elif len(parts) == 3 and parts[1] == "or":
            tree = Or(Term(parts[0]), Term(parts[2]))
            terms = [parts[0], parts[2]]
        else:
            tree = Term(parts[0])
            terms = [parts[0]]

        candidate_docs = tree.evaluate(self.index)
        if not candidate_docs:
            return []

        doc_scores = {}
        for term in terms:
            if term not in self.index:
                continue
            doc_ids, scores = self.scorer.score_array(self.index, term)
            if doc_ids.size == 0:
                continue
            mask = np.isin(doc_ids, list(candidate_docs))
            if not np.any(mask):
                continue
            filtered_doc_ids = doc_ids[mask]
            filtered_scores = scores[mask]
            for d, s in zip(filtered_doc_ids, filtered_scores):
                doc_scores[int(d)] = doc_scores.get(int(d), 0.0) + float(s)

        if not doc_scores:
            return []

        doc_ids_arr = np.array(list(doc_scores.keys()), dtype=np.int32)
        scores_arr = np.array(list(doc_scores.values()), dtype=np.float32)
        
        k = min(top_k, len(doc_ids_arr))
        if k <= 0:
            return []
            
        if k < len(scores_arr):
            part_indices = np.argpartition(scores_arr, -k)[-k:]
        else:
            part_indices = np.arange(len(scores_arr))
            
        sorted_top_indices = part_indices[np.argsort(scores_arr[part_indices])[::-1]]
        
        results = [
            SearchResult(score=float(scores_arr[i]), doc_id=int(doc_ids_arr[i]))
            for i in sorted_top_indices
        ]
        return results

def parse_query(query_str: str) -> QueryNode:
    tokens = query_str.lower().split()
    if not tokens:
        return Term("___EMPTY___")
        
    node = Term(tokens[0])
    for token in tokens[1:]:
        if token not in ("and", "or"):
            node = And(node, Term(token))
            
    return node
import heapq
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
        return {p.doc_id for p in index[self.term]}

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

        doc_scores = {doc_id: 0.0 for doc_id in candidate_docs}
        
        for term in terms:
            for posting in self.index[term]:
                if posting.doc_id in doc_scores:
                    score = self.scorer.score(self.index, term, posting)
                    doc_scores[posting.doc_id] += score
                    
        results = [SearchResult(score=s, doc_id=d) for d, s in doc_scores.items()]
        return heapq.nlargest(top_k, results)
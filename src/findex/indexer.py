import pickle
from collections import defaultdict, Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Dict, List, Iterator
from functools import cached_property
from contextlib import contextmanager

from findex.core import tokenize, timed
from findex.models import Posting, DocMeta

class Index(Mapping):
    """Об'єктно-орієнтований інвертований індекс."""
    def __init__(self):
        self._postings: Dict[str, List[Posting]] = defaultdict(list)
        self._doc_meta: Dict[int, DocMeta] = {}

    # Dunder-методи для реалізації протоколу Mapping (dict-подібна поведінка)
    def __getitem__(self, term: str) -> List[Posting]:
        return self._postings.get(term, [])

    def __iter__(self) -> Iterator[str]:
        return iter(self._postings)

    def __len__(self) -> int:
        return len(self._postings)
        
    def __contains__(self, term: object) -> bool:
        return term in self._postings
        
    def __repr__(self) -> str:
        return f"<Index: {len(self)} terms, {self.num_docs} docs>"

    @cached_property
    def num_docs(self) -> int:
        return len(self._doc_meta)
        
    @cached_property
    def avg_doc_length(self) -> float:
        if self.num_docs == 0:
            return 0.0
        total_length = sum(meta.length for meta in self._doc_meta.values())
        return total_length / self.num_docs

    def document_frequency(self, term: str) -> int:
        return len(self[term])

    def get_meta(self, doc_id: int) -> DocMeta:
        return self._doc_meta[doc_id]

    @timed
    def build(self, corpus_path: str | Path):
        path = Path(corpus_path)
        for doc_id, file_path in enumerate(path.rglob("*.txt")):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            tokens = list(tokenize(text))
            term_freqs = Counter(tokens)
            self._doc_meta[doc_id] = DocMeta(doc_id=doc_id, name=file_path.name, length=len(tokens))
            for term, freq in term_freqs.items():
                self._postings[term].append(Posting(doc_id=doc_id, frequency=freq))

    @timed
    def save(self, out_path: str):
        with open(out_path, "wb") as f:
            pickle.dump((self._postings, self._doc_meta), f)

    @timed
    def load(self, in_path: str):
        with open(in_path, "rb") as f:
            self._postings, self._doc_meta = pickle.load(f)

@contextmanager
def open_index(path: str) -> Iterator[Index]:
    """Context manager для безпечного завантаження індексу."""
    idx = Index()
    print(f"Opening index from {path}...")
    idx.load(path)
    try:
        yield idx
    finally:
        print("Closing index resources...")
        idx._postings.clear()
        idx._doc_meta.clear()
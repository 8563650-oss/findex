import pickle
import logging
import numpy as np
from collections import defaultdict, Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Dict, List, Iterator, Generator, Tuple
from functools import cached_property
from contextlib import contextmanager

from findex.core import tokenize, timed
from findex.models import DocMeta

logger = logging.getLogger("findex")

class Index(Mapping[str, Tuple[np.ndarray, np.ndarray]]):
    """Об'єктно-орієнтований інвертований індекс на основі NumPy масивів."""
    def __init__(self):
        self._postings_doc_ids: Dict[str, np.ndarray] = {}
        self._postings_freqs: Dict[str, np.ndarray] = {}
        self._doc_meta: Dict[int, DocMeta] = {}
        self._doc_lengths: np.ndarray = np.array([], dtype=np.int32)

    def __getitem__(self, term: str) -> Tuple[np.ndarray, np.ndarray]:
        if term not in self._postings_doc_ids:
            return np.array([], dtype=np.int32), np.array([], dtype=np.int32)
        return self._postings_doc_ids[term], self._postings_freqs[term]

    def __iter__(self) -> Iterator[str]:
        return iter(self._postings_doc_ids)

    def __len__(self) -> int:
        return len(self._postings_doc_ids)
        
    def __contains__(self, term: object) -> bool:
        return term in self._postings_doc_ids
        
    def __repr__(self) -> str:
        return f"<Index: {len(self)} terms, {self.num_docs} docs (NumPy)>"

    @cached_property
    def num_docs(self) -> int:
        return len(self._doc_meta)
        
    @cached_property
    def avg_doc_length(self) -> float:
        if self.num_docs == 0 or self._doc_lengths.size == 0:
            return 0.0
        return float(np.mean(self._doc_lengths))

    def document_frequency(self, term: str) -> int:
        if term not in self._postings_doc_ids:
            return 0
        return len(self._postings_doc_ids[term])

    def get_meta(self, doc_id: int) -> DocMeta:
        return self._doc_meta[doc_id]

    @timed
    def build(self, corpus_path: str | Path):
        path = Path(corpus_path)
        temp_postings = defaultdict(list)
        doc_lengths_list = []
        
        for doc_id, file_path in enumerate(sorted(path.rglob("*.txt"))):
            if file_path.is_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                tokens = list(tokenize(text))
                term_freqs = Counter(tokens)
                doc_len = len(tokens)
                doc_lengths_list.append(doc_len)
                self._doc_meta[doc_id] = DocMeta(doc_id=doc_id, name=file_path.name, length=doc_len)
                for term, freq in term_freqs.items():
                    temp_postings[term].append((doc_id, freq))
                    
        self._doc_lengths = np.array(doc_lengths_list, dtype=np.int32)
        
        for term, postings in temp_postings.items():
            postings.sort(key=lambda x: x[0])
            doc_ids = np.array([p[0] for p in postings], dtype=np.int32)
            freqs = np.array([p[1] for p in postings], dtype=np.int32)
            self._postings_doc_ids[term] = doc_ids
            self._postings_freqs[term] = freqs

    @timed
    def save(self, out_path: str):
        with open(out_path, "wb") as f:
            pickle.dump((self._postings_doc_ids, self._postings_freqs, self._doc_meta, self._doc_lengths), f)

    @timed
    def load(self, in_path: str):
        with open(in_path, "rb") as f:
            data = pickle.load(f)
            if len(data) == 4:
                self._postings_doc_ids, self._postings_freqs, self._doc_meta, self._doc_lengths = data
            else:
                old_postings, old_meta = data
                self._doc_meta = old_meta
                self._postings_doc_ids = {}
                self._postings_freqs = {}
                doc_lens = [old_meta[i].length for i in range(len(old_meta))]
                self._doc_lengths = np.array(doc_lens, dtype=np.int32)
                for term, postings in old_postings.items():
                    doc_ids = np.array([p.doc_id for p in postings], dtype=np.int32)
                    freqs = np.array([p.frequency for p in postings], dtype=np.int32)
                    self._postings_doc_ids[term] = doc_ids
                    self._postings_freqs[term] = freqs

@contextmanager
def open_index(path: str) -> Generator[Index, None, None]:
    idx = Index()
    logger.info(f"Opening index from {path}...")
    idx.load(path)
    try:
        yield idx
    finally:
        logger.info("Closing index resources...")
        idx._postings_doc_ids.clear()
        idx._postings_freqs.clear()
        idx._doc_meta.clear()
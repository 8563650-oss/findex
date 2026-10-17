import pickle
import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Any
from findex.core import tokenize
from findex.models import Posting, DocMeta

class InvertedIndex:
    def __init__(self):
        
        self.postings: Dict[str, List[Posting]] = defaultdict(list)
        
        self.doc_meta: Dict[int, DocMeta] = {}

    def build(self, corpus_path: str | Path):
        path = Path(corpus_path)
        
        # один прохід по файлах
        for doc_id, file_path in enumerate(path.rglob("*.txt")):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
            tokens = list(tokenize(text))
            term_freqs = Counter(tokens)
            
            
            self.doc_meta[doc_id] = DocMeta(doc_id=doc_id, name=file_path.name, length=len(tokens))
            
            # Оновлюємо постінги
            for term, freq in term_freqs.items():
                self.postings[term].append(Posting(doc_id=doc_id, frequency=freq))
                
        
        for term in self.postings:
            self.postings[term].sort(key=lambda p: p.doc_id)

    def save_pickle(self, out_path: str):
        """
        УВАГА: pickle небезпечний для завантаження даних з невідомих джерел. 
        Під час розпакування (unpickling) зловмисник може виконати довільний код на вашій машині!
        """
        with open(out_path, "wb") as f:
            pickle.dump((self.postings, self.doc_meta), f)

    def load_pickle(self, in_path: str):
        with open(in_path, "rb") as f:
            self.postings, self.doc_meta = pickle.load(f)

    def save_json(self, out_path: str):
        """Альтернативний, безпечний формат (JSON)."""
        data = {
            "postings": {term: [{"d": p.doc_id, "f": p.frequency} for p in posts] for term, posts in self.postings.items()},
            "doc_meta": {doc_id: {"n": m.name, "l": m.length} for doc_id, m in self.doc_meta.items()}
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
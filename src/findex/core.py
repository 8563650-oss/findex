import re
import unicodedata
from pathlib import Path
from typing import Iterator

TOKEN_PATTERN = re.compile(r"(?u)\b\w+(?:[-']\w+)*\b")

def iter_documents(corpus_path: str | Path) -> Iterator[str]:
    # ... тут ваш старий код ...
    path = Path(corpus_path)
    if not path.exists():
        raise FileNotFoundError(f"Директорію {path} не знайдено.")
    for file_path in path.rglob("*.txt"):
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                yield f.read()

def tokenize(text: str) -> Iterator[str]:
    # ... тут ваш старий код ...
    normalized_text = unicodedata.normalize("NFKC", text).lower()
    for match in TOKEN_PATTERN.finditer(normalized_text):
        yield match.group()


import time
from functools import wraps

def timed(func):
    """Декоратор для вимірювання часу виконання функції."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"[{func.__name__}] executed in {end_time - start_time:.4f} seconds.")
        return result
    return wrapper

def generate_snippet(text: str, query_terms: set[str], window: int = 80) -> str:
    """Генерує сніпет із підсвіченими термінами запиту."""
    normalized_text = text.lower()
    best_pos = -1
    
    for term in query_terms:
        pos = normalized_text.find(term)
        if pos != -1 and (best_pos == -1 or pos < best_pos):
            best_pos = pos
            
    if best_pos == -1:
        return text[:window * 2] + "..."
        
    start = max(0, best_pos - window)
    end = min(len(text), best_pos + window)
    
    snippet = text[start:end]
    for term in query_terms:
        snippet = snippet.replace(term, f"**{term.upper()}**")
        
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return prefix + snippet + suffix
import re
import unicodedata
from pathlib import Path
from typing import Iterator

# Регулярний вираз для токенізації.
# Правила:
# - Включає літери та цифри (\w).
# - Допускає дефіси та апострофи всередині слова (наприклад, "зв'язок", "будь-ласка").
# - Не захоплює пунктуацію на початку чи в кінці слова.
TOKEN_PATTERN = re.compile(r"(?u)\b\w+(?:[-']\w+)*\b")

def iter_documents(corpus_path: str | Path) -> Iterator[str]:
    """
    Генератор, що рекурсивно обходить директорію і ліниво читає текстові файли.
    Не завантажує всі документи в пам'ять одночасно.
    """
    path = Path(corpus_path)
    if not path.exists():
        raise FileNotFoundError(f"Директорію {path} не знайдено.")
        
    for file_path in path.rglob("*.txt"):
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                yield f.read()

def tokenize(text: str) -> Iterator[str]:
    """
    Генератор токенів. 
    Нормалізує Unicode (NFKC) та переводить текст у нижній регістр перед пошуком.
    """
    normalized_text = unicodedata.normalize("NFKC", text).lower()
    for match in TOKEN_PATTERN.finditer(normalized_text):
        yield match.group()
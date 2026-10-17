import pytest
from pathlib import Path
from findex.indexer import Index

@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    """Створює міні-корпус із 3 документів для тестування."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "doc0.txt").write_text("hello world from python", encoding="utf-8")
    (data_dir / "doc1.txt").write_text("hello python stream stream", encoding="utf-8")
    (data_dir / "doc2.txt").write_text("rare word here", encoding="utf-8")
    return data_dir

@pytest.fixture
def populated_index(mini_corpus: Path) -> Index:
    """Повертає вже зібраний індекс на основі mini_corpus."""
    idx = Index()
    idx.build(mini_corpus)
    return idx
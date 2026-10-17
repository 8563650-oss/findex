import pytest
from hypothesis import given, strategies as st
from typer.testing import CliRunner
from pathlib import Path
from typing import Any

from findex.cli import app
from findex.core import tokenize, generate_snippet
from findex.indexer import Index
from findex.searcher import Term, And, Or
from findex.ranking import TfIdfScorer, BM25Scorer
from findex.models import Posting

runner = CliRunner()

# --- 1. Токенізатор (10 тестів) ---
@pytest.mark.parametrize("text, expected", [
    ("Hello world", ["hello", "world"]),
    ("YOLOv8!", ["yolov8"]),
    ("Дев'ятнадцяте сторіччя", ["дев'ятнадцяте", "сторіччя"]),
    ("state-of-the-art", ["state-of-the-art"]),
    ("Розділ \u2163", ["розділ", "iv"]),
    ("   ", []),
    ("!!!", []),
    ("hello, world.", ["hello", "world"]),
    ("C++ and C#", ["c", "and", "c"]),
    ("123 456", ["123", "456"]),
])
def test_tokenizer(text: str, expected: list[str]):
    assert list(tokenize(text)) == expected

# --- 2. Сніпети (Покриття core.py - 5 тестів) ---
@pytest.mark.parametrize("text, terms, expected_in_output", [
    ("hello world python", {"python"}, "**PYTHON**"),
    ("a b c d e f g h i j k l m n o p q python", {"python"}, "..."),
    ("no match here", {"python"}, "no match here..."),
    ("python at start", {"python"}, "**PYTHON** at ..."),
    ("end is python", {"python"}, "end is **PYTHON**"),
])
def test_generate_snippet(text: str, terms: set[str], expected_in_output: str):
    snippet = generate_snippet(text, terms, window=10)
    assert expected_in_output in snippet

# --- 3. Hypothesis (Merge vs Set) ---
@given(
    st.lists(st.integers(min_value=0, max_value=100), unique=True),
    st.lists(st.integers(min_value=0, max_value=100), unique=True)
)
def test_merge_equals_set(list1: list[int], list2: list[int]):
    expected = sorted(list(set(list1) & set(list2)))
    l1, l2 = sorted(list1), sorted(list2)
    merge_res = []
    i, j = 0, 0
    while i < len(l1) and j < len(l2):
        if l1[i] == l2[j]:
            merge_res.append(l1[i])
            i += 1
            j += 1
        elif l1[i] < l2[j]:
            i += 1
        else:
            j += 1
    assert merge_res == expected

# --- 4. AST Парсер запитів (4 тести) ---
@pytest.mark.parametrize("tree, expected_docs", [
    (Term("hello"), {0, 1}),
    (And(Term("hello"), Term("stream")), {1}),
    (Or(Term("rare"), Term("stream")), {1, 2}),
    (Term("missing"), set()),
])
def test_ast_evaluation(populated_index: Index, tree: Any, expected_docs: set[int]):
    assert tree.evaluate(populated_index) == expected_docs

# --- 5. Логіка Scorer (Sanity Checks - 2 тести) ---
@pytest.mark.parametrize("scorer_class", [TfIdfScorer, BM25Scorer])
def test_scorer_sanity_checks(populated_index: Index, scorer_class: Any):
    scorer = scorer_class()
    # 1. Рідкісний термін > Частий термін
    score_rare = scorer.score(populated_index, "rare", Posting(doc_id=2, frequency=1))
    score_freq = scorer.score(populated_index, "hello", Posting(doc_id=0, frequency=1))
    assert score_rare > score_freq
    # 2. Нульовий DF (термін відсутній)
    assert scorer.score(populated_index, "missing", Posting(doc_id=0, frequency=1)) == 0.0

# --- 6. Index та CLI (5 тестів) ---
def test_index_properties_and_saveload(populated_index: Index, tmp_path: Path):
    idx = populated_index
    # type: ignore використовується для доступу до приватного поля, щоб перевірити інваріант сортування в тесті
    for _, postings in idx._postings.items():  # type: ignore # Прямий доступ до приватного поля для тестування сортування
        doc_ids = [p.doc_id for p in postings]
        assert doc_ids == sorted(doc_ids)
        
    out_file = tmp_path / "idx.bin"
    idx.save(str(out_file))
    
    idx2 = Index()
    idx2.load(str(out_file))
    assert len(idx) == len(idx2)

def test_cli_help():
    assert runner.invoke(app, ["--help"]).exit_code == 0

def test_cli_search_missing_index():
    res = runner.invoke(app, ["search", "test", "--index-path", "fake.bin"])
    assert res.exit_code == 1
    assert "not found" in res.output

def test_cli_full_pipeline(tmp_path: Path, mini_corpus: Path):
    idx_file = tmp_path / "idx.bin"
    res_idx = runner.invoke(app, ["index", str(mini_corpus), "--out", str(idx_file)])
    assert res_idx.exit_code == 0
    
    res_search = runner.invoke(app, ["search", "python AND stream", "--index-path", str(idx_file)])
    assert res_search.exit_code == 0
    assert "python" in res_search.output

    res_json = runner.invoke(app, ["search", "python AND stream", "--index-path", str(idx_file), "--json"])
    assert res_json.exit_code == 0
    assert "doc_id" in res_json.output
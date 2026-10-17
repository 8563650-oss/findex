from findex.core import tokenize

def test_tokenize_basic():
    text = "Hello World! 123"
    assert list(tokenize(text)) == ["hello", "world", "123"]

def test_tokenize_apostrophe_and_hyphen():
    text = "Дев'ятнадцяте сторіччя — це час будь-яких змін."
    tokens = list(tokenize(text))
    assert "дев'ятнадцяте" in tokens
    assert "будь-яких" in tokens
    assert "—" not in tokens

def test_tokenize_unicode_normalization():
    
    text = "Розділ \u2163"
    assert list(tokenize(text)) == ["розділ", "iv"]

def test_tokenize_punctuation_stripping():
    text = "...word!!!, test."
    assert list(tokenize(text)) == ["word", "test"]
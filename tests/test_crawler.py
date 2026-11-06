import pytest
import httpx
from typing import Any
from findex.crawler import canonicalize_url, Crawler

def test_canonicalize_url():
    assert canonicalize_url("HTTP://Example.COM/path#frag") == "http://example.com/path"
    assert canonicalize_url("https://a.com/?b=2&a=1") == "https://a.com/?a=1&b=2"
    assert canonicalize_url("http://test.com") == "http://test.com/"

@pytest.mark.asyncio
async def test_crawler_mocked_network(monkeypatch: pytest.MonkeyPatch):
    """Тест краулера за допомогою httpx.MockTransport (без виходу в інтернет)."""
    
    def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "robots.txt" in url:
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        elif "page1" in url:
            html = "<html><body><a href='/page2'>Link</a></body></html>"
            return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})
        elif "page2" in url:
            return httpx.Response(200, text="End", headers={"Content-Type": "text/html"})
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    
    # Замість lambda використовуємо типізовану функцію, щоб Pyright був задоволений
    def mock_transport_factory(*args: Any, **kwargs: Any) -> httpx.MockTransport:
        return mock_transport
        
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", mock_transport_factory)
    
    crawler = Crawler("http://test.com/page1", max_pages=2, concurrency=1)
    pages = [p async for p in crawler.crawl()]
    
    assert len(pages) == 2
    assert pages[0].url == "http://test.com/page1"
    assert pages[1].url == "http://test.com/page2"
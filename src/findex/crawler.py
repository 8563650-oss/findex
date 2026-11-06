import asyncio
import logging
import random
import urllib.robotparser
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
from typing import AsyncGenerator
import httpx
from selectolax.lexbor import LexborHTMLParser
from findex.models import CrawledPage

logger = logging.getLogger("findex.crawler")

def canonicalize_url(url: str) -> str:
    """Нормалізує URL: нижній регістр схеми/хоста, видалення фрагмента, сортування параметрів."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path if parsed.path else "/"
    
    query_params = parse_qsl(parsed.query)
    query_params.sort()
    query = urlencode(query_params)
    
    return urlunparse((scheme, netloc, path, parsed.params, query, ""))

class RobotsCache:
    """Асинхронний кеш файлів robots.txt для кожного хоста."""
    def __init__(self, client: httpx.AsyncClient, user_agent: str):
        self.client = client
        self.user_agent = user_agent
        self._cache: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host_url = f"{parsed.scheme}://{parsed.netloc}"
        
        async with self._lock:
            if host_url not in self._cache:
                robots_url = f"{host_url}/robots.txt"
                parser = urllib.robotparser.RobotFileParser()
                parser.set_url(robots_url)
                try:
                    response = await self.client.get(robots_url, timeout=5.0)
                    if response.status_code == 200:
                        parser.parse(response.text.splitlines())
                except (httpx.RequestError, asyncio.TimeoutError):
                    logger.warning(f"Could not fetch {robots_url}. Assuming allowed.")
                self._cache[host_url] = parser

        parser = self._cache[host_url]
        return parser.can_fetch(self.user_agent, url)

class Crawler:
    def __init__(self, 
                 start_url: str, 
                 max_pages: int = 200, 
                 concurrency: int = 20, 
                 user_agent: str = "FindexBot/1.0 (Student Project; your@email.com)"):
        self.start_url = canonicalize_url(start_url)
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.user_agent = user_agent
        self.headers = {"User-Agent": user_agent}
        
        self.pages_crawled = 0
        self.in_flight_requests = 0
        self.errors = 0
        self.seen_urls: set[str] = set()

    async def fetch_with_retry(self, client: httpx.AsyncClient, url: str, max_retries: int = 3) -> httpx.Response | None:
        """Виконує HTTP GET із exponential backoff та jitter для обробки 429 та 5xx."""
        backoff = 1.0
        for attempt in range(max_retries):
            self.in_flight_requests += 1
            try:
                async with asyncio.timeout(10.0):
                    response = await client.get(url, headers=self.headers, follow_redirects=True)
                    
                if response.status_code in {429, 500, 502, 503, 504}:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_time = int(retry_after)
                    else:
                        wait_time = backoff + random.uniform(0, 0.5)
                        backoff *= 2
                    
                    logger.warning(f"[{url}] HTTP {response.status_code}. Retrying in {wait_time:.2f}s (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                    
                return response
                
            except (httpx.RequestError, TimeoutError) as e:
                logger.error(f"[{url}] Failed: {str(e)}. Retrying... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(backoff + random.uniform(0, 0.5))
                backoff *= 2
            finally:
                self.in_flight_requests -= 1
                
        self.errors += 1
        return None

    async def crawl(self) -> AsyncGenerator[CrawledPage, None]:
        url_queue: asyncio.Queue[str] = asyncio.Queue()
        await url_queue.put(self.start_url)
        self.seen_urls.add(self.start_url)
        
        # Черга для готових сторінок, щоб відокремити воркери від генератора
        result_queue: asyncio.Queue[CrawledPage] = asyncio.Queue()
        
        sem = asyncio.Semaphore(self.concurrency)
        host_locks: dict[str, asyncio.Lock] = {}
        transport = httpx.AsyncHTTPTransport(retries=0)
        
        async with httpx.AsyncClient(transport=transport) as client:
            robots_cache = RobotsCache(client, self.user_agent)
            
            async def worker():
                while self.pages_crawled < self.max_pages:
                    try:
                        url = await asyncio.wait_for(url_queue.get(), timeout=1.0)
                    except TimeoutError:
                        if self.in_flight_requests > 0:
                            continue
                        break
                        
                    parsed = urlparse(url)
                    host = parsed.netloc
                    if host not in host_locks:
                        host_locks[host] = asyncio.Lock()
                        
                    async with sem:
                        async with host_locks[host]:
                            if not await robots_cache.is_allowed(url):
                                logger.info(f"[{url}] Blocked by robots.txt")
                                url_queue.task_done()
                                continue
                                
                            start_fetch = asyncio.get_running_loop().time()
                            response = await self.fetch_with_retry(client, url)
                            fetch_time = asyncio.get_running_loop().time() - start_fetch
                            await asyncio.sleep(0.5) # Пауза між запитами на хост
                            
                    if response and response.status_code == 200:
                        content_type = response.headers.get("Content-Type", "")
                        if "text/html" in content_type:
                            html = response.text
                            parser = LexborHTMLParser(html)
                            text = parser.text(separator=' ', strip=True)
                            
                            links = []
                            for node in parser.css('a[href]'):
                                href = node.attributes.get('href')
                                if href:
                                    absolute_url = urljoin(url, href)
                                    canon_url = canonicalize_url(absolute_url)
                                    links.append(canon_url)
                                    
                                    if canon_url.startswith("http") and canon_url not in self.seen_urls:
                                        self.seen_urls.add(canon_url)
                                        await url_queue.put(canon_url)
                                        
                            page = CrawledPage(
                                url=url,
                                status=response.status_code,
                                content=html,
                                text=text,
                                links=links,
                                fetch_time=fetch_time
                            )
                            await result_queue.put(page)
                    
                    url_queue.task_done()

            # Використовуємо TaskGroup, як того вимагає лаба
            try:
                async with asyncio.TaskGroup() as tg:
                    workers = [tg.create_task(worker()) for _ in range(self.concurrency)]
                    
                    while self.pages_crawled < self.max_pages:
                        try:
                            # Очікуємо готову сторінку від будь-якого воркера
                            page = await asyncio.wait_for(result_queue.get(), timeout=1.0)
                            self.pages_crawled += 1
                            yield page
                        except TimeoutError:
                            # Якщо черга результатів порожня, перевіряємо, чи є ще живі воркери
                            if all(w.done() for w in workers):
                                break
                    
                    # На max_pages воркери скасовуються (вимога з опису лаби)
                    for w in workers:
                        if not w.done():
                            w.cancel()
                            
            except Exception as e:
                logger.error(f"Crawler error: {e}")
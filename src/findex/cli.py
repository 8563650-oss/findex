import json
import time
import logging
import asyncio
import os
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.live import Live
from rich.table import Table
from findex.indexer import Index, open_index
from findex.searcher import parse_query
from findex.ranking import BM25Scorer

# from findex.crawler import Crawler

app = typer.Typer()
console = Console()

@app.command("index")
def index_command(
    corpus: Path = typer.Argument(...),
    out: Path = typer.Option(..., "--out", "-o")
):
    idx = Index()
    idx.build(corpus)
    idx.save(str(out))
    console.print(f"[green]Index built and saved to {out}[/green]")

@app.command("search")
def search_command(
    query: str = typer.Argument(...),
    index_path: str = typer.Option("index.bin", "--index-path", "-i"),
    json_output: bool = typer.Option(False, "--json")
):
    if not Path(index_path).exists():
        console.print(f"Index file {index_path} not found.", style="red")
        raise typer.Exit(1)
        
    with open_index(index_path) as idx:
        ast = parse_query(query)
        docs = ast.evaluate(idx)
        
        scorer = BM25Scorer()
        results = []
        for doc_id in docs:
            score = scorer.score(idx, query, idx._postings.get(query, [])[0]) if query in idx else 0.0
            results.append((doc_id, score))
            
        results.sort(key=lambda x: x[1], reverse=True)
        
        if json_output:
            out_data = [{"doc_id": d, "score": s} for d, s in results]
            console.print(json.dumps(out_data))
        else:
            for d, s in results:
                meta = idx.get_meta(d)
                console.print(f"[[{d}]] {meta.name} (Score: {s:.4f})")

@app.command("crawl")
def crawl_command(
    start_url: str = typer.Argument(...),
    out: Path = typer.Option(..., "--out", "-o"),
    max_pages: int = typer.Option(200),
    concurrency: int = typer.Option(20)
):
    file_handler = logging.FileHandler("crawl.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    crawler_logger = logging.getLogger("findex.crawler")
    crawler_logger.setLevel(logging.INFO)
    crawler_logger.addHandler(file_handler)

    crawler = Crawler(start_url, max_pages=max_pages, concurrency=concurrency)
    start_time = time.perf_counter()

    def generate_table() -> Table:
        table = Table(title="Spider Status")
        table.add_column("Метрика", style="cyan")
        table.add_column("Значення", style="magenta")
        
        elapsed = time.perf_counter() - start_time
        rps = crawler.pages_crawled / elapsed if elapsed > 0 else 0
        
        table.add_row("Зібрано сторінок", str(crawler.pages_crawled))
        table.add_row("Швидкість (стор/сек)", f"{rps:.2f}")
        table.add_row("Запитів у польоті", str(crawler.in_flight_requests))
        table.add_row("Помилок", str(crawler.errors))
        return table

    async def run() -> None:
        with out.open("w", encoding="utf-8") as f:
            with Live(generate_table(), refresh_per_second=4) as live:
                async for page in crawler.crawl():
                    record = {
                        "url": page.url,
                        "status": page.status,
                        "content": page.content,
                        "text": page.text,
                        "links": page.links,
                        "fetch_time": page.fetch_time
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    live.update(generate_table())
                    
    asyncio.run(run())
    console.print(f"[green]Краулінг завершено! Дані збережено у {out}. Лог: crawl.log[/green]")

@app.command("serve")
def serve_command(
    port: int = typer.Option(8000, "--port", "-p"),
    workers: int = typer.Option(1, "--workers", "-w"),
    index_path: str = typer.Option("index.bin", "--index", "-i")
):
    os.environ["INDEX_PATH"] = index_path
    console.print(f"[green]Starting FastAPI server on port {port} with {workers} worker(s)...[/green]")
    console.print(f"[cyan]Using index file: {index_path}[/cyan]")
    uvicorn.run("findex.web.app:app", host="0.0.0.0", port=port, workers=workers)

if __name__ == "__main__":
    app()
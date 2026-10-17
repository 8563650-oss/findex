import typer
import logging
import json
import sys
from pathlib import Path
from typing import Literal
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from findex.indexer import Index, open_index
from findex.ranking import BM25Scorer, TfIdfScorer
from findex.searcher import RankedSearcher
from findex.core import generate_snippet

app = typer.Typer(help="Findex: A custom local search engine.")
console = Console(stderr=True) # Діагностика йде в stderr
result_console = Console()     # Результати йдуть в stdout

def setup_logging(verbose: int):
    logger = logging.getLogger("findex")
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    if verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

@app.callback()
def main(
    v: int = typer.Option(0, "-v", count=True, help="Increase logging verbosity (-v for INFO, -vv for DEBUG)")
):
    setup_logging(v)

@app.command()
def index(
    corpus: Path = typer.Argument(..., help="Path to corpus directory"),
    out: Path = typer.Option(Path("index.bin"), help="Output index file")
):
    """Build the inverted index from a corpus of text files."""
    idx = Index()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description=f"Building index from {corpus}...", total=None)
        idx.build(corpus)
        idx.save(str(out))
    console.print(f"[green]Successfully built and saved index to {out}[/green]")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    index_path: Path = typer.Option(Path("index.bin"), help="Path to saved index.bin"),
    scorer_name: Literal["bm25", "tfidf"] = typer.Option("bm25", help="Ranking algorithm"),
    top_k: int = typer.Option(5, help="Number of results to show"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON to stdout")
):
    """Search the index."""
    if not index_path.exists():
        console.print(f"[red]Error: Index file '{index_path}' not found. Run 'findex index' first.[/red]")
        raise typer.Exit(code=1)

    scorer = BM25Scorer() if scorer_name == "bm25" else TfIdfScorer()
    
    with open_index(str(index_path)) as idx:
        searcher = RankedSearcher(idx, scorer)
        results = searcher.search(query, top_k=top_k)
        
        if as_json:
            # Якщо --json, пишемо тільки дані в stdout
            output = [{"doc_id": r.doc_id, "score": r.score} for r in results]
            result_console.print(json.dumps(output))
            return

        table = Table(title=f"Search Results for '{query}' (Scorer: {scorer_name.upper()})")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Score", justify="right", style="magenta")
        table.add_column("Doc ID", style="blue")
        table.add_column("Snippet")

        for i, hit in enumerate(results):
            meta = idx.get_meta(hit.doc_id)
            filepath = Path("data") / meta.name
            
            if filepath.exists():
                text = filepath.read_text(encoding="utf-8")
                snippet = generate_snippet(text, set(query.lower().split()), window=40)
                # Видаляємо маркдаун для консолі та замінюємо на rich-теги
                snippet = snippet.replace("**", "[bold yellow]").replace("**", "[/bold yellow]")
            else:
                snippet = "[red]File missing[/red]"
                
            table.add_row(str(i+1), f"{hit.score:.4f}", str(hit.doc_id), snippet)

        result_console.print(table)

if __name__ == "__main__":
    app()
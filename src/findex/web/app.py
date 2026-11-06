import logging
import time
import math
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from findex.indexer import Index
from findex.searcher import parse_query
from findex.ranking import BM25Scorer
from findex.web.config import get_settings

logger = logging.getLogger("findex.web")

index_instance: Index | None = None
scorer = BM25Scorer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global index_instance
    settings = get_settings()
    try:
        idx = Index()
        logger.info(f"Завантаження індексу з {settings.index_path}...")
        idx.load(settings.index_path)
        index_instance = idx
        logger.info("Індекс успішно завантажено!")
        yield
    except FileNotFoundError:
        logger.error(f"Файл індексу {settings.index_path} не знайдено.")
        yield
    except Exception as e:
        logger.error(f"Помилка завантаження індексу: {e}")
        yield
    finally:
        if index_instance is not None:
            index_instance._postings.clear()  # type: ignore
            index_instance._doc_meta.clear()  # type: ignore
            index_instance = None

app = FastAPI(title="Findex Web Search", lifespan=lifespan)

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

def get_index() -> Index:
    if index_instance is None:
        raise HTTPException(status_code=503, detail="Індекс ще не завантажений або недоступний")
    return index_instance

class SearchResultItem(BaseModel):
    doc_id: int
    name: str
    score: float
    snippet: str

class SearchResponse(BaseModel):
    query: str
    total_results: int
    page: int
    total_pages: int
    results: list[SearchResultItem]
    time_ms: float

class DocResponse(BaseModel):
    doc_id: int
    name: str
    length: int

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "query": "",
        "results": None,
        "total_results": 0,
        "time_ms": 0.0
    })

@app.get("/search-ui", response_class=HTMLResponse)
def search_ui(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    idx: Index = Depends(get_index)
):
    start_time = time.perf_counter()
    try:
        ast = parse_query(q)
        matched_docs = ast.evaluate(idx)
    except Exception:
        matched_docs = set()
        
    results = []
    for doc_id in matched_docs:
        terms = set(q.lower().split())
        total_score = sum(scorer.score(idx, t, idx._postings.get(t, [])[0]) 
                          for t in terms if t in idx and len(idx._postings.get(t, [])) > 0)
        meta = idx.get_meta(doc_id)
        results.append(SearchResultItem(
            doc_id=doc_id,
            name=meta.name,
            score=total_score,
            snippet=f"Документ містить збіги за запитом '{q}'..."
        ))
        
    results.sort(key=lambda x: x.score, reverse=True)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    return templates.TemplateResponse(request, "index.html", {
        "query": q,
        "results": results,
        "total_results": len(results),
        "time_ms": elapsed_ms
    })

@app.get("/health")
def health_check(idx: Index = Depends(get_index)):
    return {"status": "ok", "docs": idx.num_docs}

@app.get("/stats")
def get_stats(idx: Index = Depends(get_index)):
    return {
        "num_docs": idx.num_docs,
        "vocab_size": len(idx),
        "avg_doc_length": idx.avg_doc_length
    }

@app.get("/search", response_model=SearchResponse)
def search_api(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    idx: Index = Depends(get_index)
):
    start_time = time.perf_counter()
    try:
        ast = parse_query(q)
        matched_docs = ast.evaluate(idx)
    except Exception:
        matched_docs = set()
        
    results = []
    for doc_id in matched_docs:
        terms = set(q.lower().split())
        total_score = sum(scorer.score(idx, t, idx._postings.get(t, [])[0]) 
                          for t in terms if t in idx and len(idx._postings.get(t, [])) > 0)
        meta = idx.get_meta(doc_id)
        results.append(SearchResultItem(
            doc_id=doc_id,
            name=meta.name,
            score=total_score,
            snippet=f"Результат знайдено в документі {meta.name}..."
        ))
        
    results.sort(key=lambda x: x.score, reverse=True)
    total_results = len(results)
    total_pages = math.ceil(total_results / limit) if total_results > 0 else 1
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_results = results[start_idx:end_idx]
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    return SearchResponse(
        query=q,
        total_results=total_results,
        page=page,
        total_pages=total_pages,
        results=page_results,
        time_ms=elapsed_ms
    )

@app.get("/docs/{doc_id}", response_model=DocResponse)
def get_document(doc_id: int, idx: Index = Depends(get_index)):
    try:
        meta = idx.get_meta(doc_id)
        return DocResponse(doc_id=meta.doc_id, name=meta.name, length=meta.length)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Документ з id {doc_id} не знайдено")

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import uuid
    error_id = str(uuid.uuid4())
    logger.error(f"Unexpected error [{error_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_id": error_id}
    )
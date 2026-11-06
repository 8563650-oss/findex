from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    frequency: int

@dataclass(frozen=True, slots=True)
class DocMeta:
    doc_id: int
    name: str
    length: int

@dataclass(frozen=True, slots=True)
class CrawledPage:
    url: str
    status: int
    content: str
    text: str
    links: list[str]
    fetch_time: float
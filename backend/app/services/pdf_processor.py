from dataclasses import dataclass
from io import BytesIO
from typing import List

from pypdf import PdfReader

from app.config import settings


@dataclass
class PageText:
    page_number: int
    text: str


@dataclass
class Chunk:
    text: str
    page: int


def extract_pages(file_bytes: bytes) -> List[PageText]:
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(PageText(page_number=i, text=text))
    return pages


def chunk_pages(
    pages: List[PageText],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Chunk]:
    """Simple sliding-window chunking, tracking the source page per chunk."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    chunks: List[Chunk] = []
    for page in pages:
        text = page.text
        start = 0
        text_len = len(text)
        if text_len == 0:
            continue
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(text=chunk_text, page=page.page_number))
            if end == text_len:
                break
            start = end - chunk_overlap
    return chunks

from typing import List, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int
    blob_url: Optional[str] = None
    already_indexed: bool = False


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # restrict search to one document if provided
    top_k: Optional[int] = None


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    page: Optional[int] = None
    chunk_id: str
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]

import uuid
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.config import settings
from app.services.pdf_processor import Chunk

_search_client = None


def _get_client() -> SearchClient:
    global _search_client
    if _search_client is None:
        _search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
        )
    return _search_client


def index_chunks(
    document_id: str,
    filename: str,
    chunks: List[Chunk],
    embeddings: List[List[float]],
) -> int:
    """Uploads chunk text + vectors to Azure AI Search. Returns count indexed."""
    documents = []
    for chunk, embedding in zip(chunks, embeddings):
        documents.append(
            {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "filename": filename,
                "page": chunk.page,
                "content": chunk.text,
                "content_vector": embedding,
            }
        )

    if not documents:
        return 0

    result = _get_client().upload_documents(documents=documents)
    return sum(1 for r in result if r.succeeded)


def find_by_filename(filename: str) -> Optional[dict]:
    """Returns {document_id, filename, chunk_count} if a document with this
    exact filename is already indexed, else None."""
    escaped = filename.replace("'", "''")
    results = list(
        _get_client().search(
            search_text="*",
            filter=f"filename eq '{escaped}'",
            select=["document_id", "filename"],
            top=1000,
        )
    )
    if not results:
        return None
    return {
        "document_id": results[0]["document_id"],
        "filename": results[0]["filename"],
        "chunk_count": len(results),
    }


def list_documents() -> List[dict]:
    """Returns one summary entry per distinct uploaded document."""
    results = list(
        _get_client().search(
            search_text="*",
            select=["document_id", "filename"],
            top=1000,
        )
    )
    summaries: dict[str, dict] = {}
    for r in results:
        doc_id = r["document_id"]
        if doc_id not in summaries:
            summaries[doc_id] = {
                "document_id": doc_id,
                "filename": r["filename"],
                "chunk_count": 0,
            }
        summaries[doc_id]["chunk_count"] += 1
    return list(summaries.values())


def delete_document(document_id: str) -> int:
    """Deletes all indexed chunks for a document_id. Returns count deleted."""
    uuid.UUID(document_id)  # validate before use in filter
    results = list(
        _get_client().search(
            search_text="*",
            filter=f"document_id eq '{document_id}'",
            select=["id"],
            top=1000,
        )
    )
    if not results:
        return 0
    result = _get_client().delete_documents(documents=[{"id": r["id"]} for r in results])
    return sum(1 for r in result if r.succeeded)


def hybrid_search(
    query_text: str,
    query_vector: List[float],
    top_k: int,
    document_id: Optional[str] = None,
):
    """Runs a hybrid (keyword + vector) search, optionally scoped to one document."""
    vector_query = VectorizedQuery(
        vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector"
    )

    filter_expr = None
    if document_id:
        # document_id is always a server-generated UUID; validate before interpolating
        # into the OData filter to avoid filter injection.
        uuid.UUID(document_id)
        filter_expr = f"document_id eq '{document_id}'"

    results = _get_client().search(
        search_text=query_text,
        vector_queries=[vector_query],
        filter=filter_expr,
        select=["id", "document_id", "filename", "page", "content"],
        top=top_k,
    )
    return list(results)

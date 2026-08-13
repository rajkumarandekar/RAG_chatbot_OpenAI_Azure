from typing import List

from fastapi import APIRouter, HTTPException

from app.models import DocumentSummary
from app.services import blob_storage, search_service

router = APIRouter()


@router.get("/documents", response_model=List[DocumentSummary])
async def list_documents():
    return search_service.list_documents()


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    try:
        chunks_deleted = search_service.delete_document(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id.")

    if chunks_deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found.")

    blobs_deleted = blob_storage.delete_document_blobs(document_id)

    return {
        "document_id": document_id,
        "chunks_deleted": chunks_deleted,
        "blobs_deleted": blobs_deleted,
    }

from typing import List

from fastapi import APIRouter

from app.models import DocumentSummary
from app.services import search_service

router = APIRouter()


@router.get("/documents", response_model=List[DocumentSummary])
async def list_documents():
    return search_service.list_documents()

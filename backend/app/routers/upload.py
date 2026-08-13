from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models import UploadResponse
from app.services import blob_storage, openai_service, pdf_processor, search_service

router = APIRouter()

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 25 MB limit.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 0. Skip re-processing (re-embedding, re-indexing) if this filename was
    # already uploaded, to avoid burning free-tier quota on duplicates.
    existing = search_service.find_by_filename(file.filename)
    if existing:
        return UploadResponse(
            document_id=existing["document_id"],
            filename=existing["filename"],
            chunks_indexed=existing["chunk_count"],
            already_indexed=True,
        )

    # 1. Store the original PDF in Blob Storage
    document_id, blob_url = blob_storage.upload_pdf(file_bytes, file.filename)

    # 2. Extract text per page
    pages = pdf_processor.extract_pages(file_bytes)
    if not pages:
        raise HTTPException(
            status_code=422, detail="No extractable text found in this PDF."
        )

    # 3. Split into overlapping chunks, keeping page numbers
    chunks = pdf_processor.chunk_pages(pages)
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not derive chunks from PDF text.")

    # 4. Generate embeddings for each chunk
    embeddings = openai_service.embed_texts([c.text for c in chunks])

    # 5. Index chunk text + vectors in Azure AI Search
    indexed_count = search_service.index_chunks(
        document_id=document_id,
        filename=file.filename,
        chunks=chunks,
        embeddings=embeddings,
    )

    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        chunks_indexed=indexed_count,
        blob_url=blob_url,
    )

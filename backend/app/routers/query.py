from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import QueryRequest, QueryResponse, SourceChunk
from app.services import openai_service, search_service

router = APIRouter()

_GREETINGS = {
    "hi", "hii", "hiii", "hello", "hey", "heyy", "yo",
    "good morning", "good afternoon", "good evening",
}


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    # Skip the embed + search + LLM round trip for plain greetings.
    if question.lower().strip("!.? ") in _GREETINGS:
        return QueryResponse(
            answer="Hello! Upload a PDF and ask me anything about it.",
            sources=[],
        )

    top_k = request.top_k or settings.TOP_K

    # 1. Embed the question with the same embedding deployment used for chunks
    query_vector = openai_service.embed_text(question)

    # 2. Hybrid (keyword + vector) search in Azure AI Search
    results = search_service.hybrid_search(
        query_text=question,
        query_vector=query_vector,
        top_k=top_k,
        document_id=request.document_id,
    )

    if not results:
        return QueryResponse(
            answer="I couldn't find any relevant content. Try uploading a document first.",
            sources=[],
        )

    # 3. Send retrieved chunks + question to the chat LLM deployment
    context_chunks = [r["content"] for r in results]
    answer = openai_service.generate_answer(question, context_chunks)

    sources = [
        SourceChunk(
            document_id=r["document_id"],
            filename=r["filename"],
            page=r.get("page"),
            chunk_id=r["id"],
            excerpt=r["content"][:300],
            score=r.get("@search.score", 0.0),
        )
        for r in results
    ]

    return QueryResponse(answer=answer, sources=sources)

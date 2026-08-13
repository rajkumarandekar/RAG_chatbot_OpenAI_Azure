import time
from typing import List

from openai import AzureOpenAI, NotFoundError

from app.config import settings

_client = None

_RETRYABLE_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 2


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
    return _client


def _with_retry(fn):
    """Azure's Global Standard deployment routing occasionally 404s
    (DeploymentNotFound) on a fresh/valid deployment; retrying briefly
    resolves it."""
    last_error = None
    for attempt in range(_RETRYABLE_ATTEMPTS):
        try:
            return fn()
        except NotFoundError as e:
            last_error = e
            if attempt < _RETRYABLE_ATTEMPTS - 1:
                time.sleep(_RETRY_DELAY_SECONDS)
    raise last_error


def embed_text(text: str) -> List[float]:
    response = _with_retry(
        lambda: _get_client().embeddings.create(
            input=text,
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        )
    )
    return response.data[0].embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    response = _with_retry(
        lambda: _get_client().embeddings.create(
            input=texts,
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        )
    )
    return [item.embedding for item in response.data]


SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using ONLY the provided "
    "document excerpts. If the answer is not contained in the excerpts, say you "
    "don't know. Always be concise and cite page numbers when relevant."
)


def generate_answer(question: str, context_chunks: List[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    user_prompt = (
        f"Document excerpts:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the excerpts above."
    )

    response = _with_retry(
        lambda: _get_client().chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    )
    return response.choices[0].message.content

import uuid
from azure.storage.blob import BlobServiceClient, ContentSettings

from app.config import settings

_blob_service_client = None


def _get_blob_service_client() -> BlobServiceClient:
    global _blob_service_client
    if _blob_service_client is None:
        _blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
    return _blob_service_client


def _get_container_client():
    container_client = _get_blob_service_client().get_container_client(
        settings.AZURE_STORAGE_CONTAINER_NAME
    )
    if not container_client.exists():
        container_client.create_container()
    return container_client


def upload_pdf(file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    """Uploads the raw PDF to Blob Storage. Returns (document_id, blob_url)."""
    document_id = str(uuid.uuid4())
    blob_name = f"{document_id}/{original_filename}"

    container_client = _get_container_client()
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        file_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/pdf"),
    )

    return document_id, blob_client.url


def delete_document_blobs(document_id: str) -> int:
    """Deletes all blobs under the document_id/ prefix. Returns count deleted."""
    container_client = _get_container_client()
    deleted = 0
    for blob in container_client.list_blobs(name_starts_with=f"{document_id}/"):
        container_client.delete_blob(blob.name)
        deleted += 1
    return deleted

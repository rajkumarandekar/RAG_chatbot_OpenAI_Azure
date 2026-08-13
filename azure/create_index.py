"""
One-time script to create (or update) the Azure AI Search index used by this app.
Run locally with the backend's virtualenv active:

    python azure/create_index.py

Reads the same env vars as the backend (AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY,
AZURE_SEARCH_INDEX_NAME) — set them in backend/.env or export them before running.
"""
import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)

ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT", "<AZURE_SEARCH_ENDPOINT>")
API_KEY = os.environ.get("AZURE_SEARCH_API_KEY", "<AZURE_SEARCH_API_KEY>")
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "<AZURE_SEARCH_INDEX_NAME>")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))


def main():
    client = SearchIndexClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="filename", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="page", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="rag-vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="rag-hnsw",
                parameters=HnswParameters(m=4, ef_construction=400, ef_search=500, metric=VectorSearchAlgorithmMetric.COSINE),
            )
        ],
        profiles=[VectorSearchProfile(name="rag-vector-profile", algorithm_configuration_name="rag-hnsw")],
    )

    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="rag-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")]
                ),
            )
        ]
    )

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )

    client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' created/updated successfully.")


if __name__ == "__main__":
    main()

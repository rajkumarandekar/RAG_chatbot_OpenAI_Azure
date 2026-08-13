"""
Centralized configuration loaded from environment variables.
All Azure resource details are placeholders until provided — see backend/.env.example.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Azure Blob Storage ---
    AZURE_STORAGE_CONNECTION_STRING: str = "<AZURE_STORAGE_CONNECTION_STRING>"
    AZURE_STORAGE_CONTAINER_NAME: str = "<AZURE_STORAGE_CONTAINER_NAME>"

    # --- Azure OpenAI ---
    AZURE_OPENAI_ENDPOINT: str = "<AZURE_OPENAI_ENDPOINT>"
    AZURE_OPENAI_API_KEY: str = "<AZURE_OPENAI_API_KEY>"
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "<AZURE_OPENAI_CHAT_DEPLOYMENT>"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "<AZURE_OPENAI_EMBEDDING_DEPLOYMENT>"

    # --- Azure AI Search ---
    AZURE_SEARCH_ENDPOINT: str = "<AZURE_SEARCH_ENDPOINT>"
    AZURE_SEARCH_API_KEY: str = "<AZURE_SEARCH_API_KEY>"
    AZURE_SEARCH_INDEX_NAME: str = "<AZURE_SEARCH_INDEX_NAME>"

    # --- App behavior ---
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 5
    EMBEDDING_DIMENSIONS: int = 1536

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:5173"


settings = Settings()

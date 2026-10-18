import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

class Settings(BaseSettings):
    # LLM Provider configuration
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    llm_provider: str = "groq"  # "groq" | "gemini" | "mock"
    
    # Database
    postgres_url: str = "sqlite:///./chatbot.db"
    
    # Security
    environment: str = "development"  # "development" | "staging" | "production" | "testing"
    secret_key: str = "super-secret-jwt-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # Chroma & Vector Store
    chroma_persist_dir: str = os.path.join(os.path.dirname(__file__), "chroma_data")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Retrieval configuration
    vector_top_k: int = 10
    bm25_top_k: int = 10
    final_top_k: int = 5
    enable_reranker: bool = True
    reranker_type: str = "semantic_lexical"  # "semantic_lexical" | "cross_encoder" | "passthrough"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    confidence_threshold: float = 0.25
    
    # Uploads
    upload_dir: str = os.path.join(os.path.dirname(__file__), "uploads")
    max_upload_size_mb: int = 25

    @property
    def cors_origins_list(self) -> list:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=(ENV_PATH, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()


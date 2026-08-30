import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

class Settings(BaseSettings):
    # LLM Provider configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    llm_provider: str = "gemini"  # "gemini" | "mock"
    
    # Database
    postgres_url: str = "sqlite:///./chatbot.db"
    
    # Security
    secret_key: str = "super-secret-jwt-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # Chroma & Vector Store
    chroma_persist_dir: str = os.path.join(os.path.dirname(__file__), "chroma_data")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Retrieval configuration
    vector_top_k: int = 10
    bm25_top_k: int = 10
    final_top_k: int = 5
    enable_reranker: bool = True
    confidence_threshold: float = 0.25
    
    # Uploads
    upload_dir: str = os.path.join(os.path.dirname(__file__), "uploads")

    model_config = SettingsConfigDict(
        env_file=(ENV_PATH, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()


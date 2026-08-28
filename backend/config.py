import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

class Settings(BaseSettings):
    gemini_api_key: str = ""
    postgres_url: str = "postgresql://chatbot:chatbot123@localhost:5432/chatbot_db"
    secret_key: str = "super-secret-jwt-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    chroma_persist_dir: str = os.path.join(os.path.dirname(__file__), "chroma_data")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    gemini_model: str = "gemini-3.6-flash"
    retrieval_k: int = 5
    confidence_threshold: float = 0.25

    model_config = SettingsConfigDict(
        env_file=(ENV_PATH, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

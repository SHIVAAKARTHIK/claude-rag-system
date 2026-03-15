from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "multimodal-rag"
    PINECONE_DIMENSION: int = 1536

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_CHAT_MODEL: str = "gpt-4o"

    # Storage — all files go into .tmp/uploads/
    UPLOAD_DIR: str = "./.tmp/uploads"
    FRAMES_DIR: str = "./.tmp/uploads/frames"
    THUMBNAILS_DIR: str = "./.tmp/uploads/thumbnails"
    METADATA_DIR: str = "./.tmp/uploads/metadata"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    @field_validator("MAX_UPLOAD_SIZE", mode="before")
    @classmethod
    def parse_upload_size(cls, v):
        if isinstance(v, str):
            v = v.strip().upper()
            if v.endswith("MB"):
                return int(v[:-2]) * 1024 * 1024
            if v.endswith("KB"):
                return int(v[:-2]) * 1024
            if v.endswith("GB"):
                return int(v[:-2]) * 1024 * 1024 * 1024
        return int(v)

    # Processing
    VIDEO_MAX_FRAMES: int = 10
    DOCUMENT_CHUNK_SIZE: int = 500
    DOCUMENT_CHUNK_OVERLAP: int = 50
    SEARCH_TOP_K: int = 10

    # API
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"


settings = Settings()

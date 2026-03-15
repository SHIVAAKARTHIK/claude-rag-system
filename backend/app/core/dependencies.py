from functools import lru_cache
from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.services.llm_service import LLMService
from app.services.document_processing import DocumentProcessingService
from app.services.video_processing import VideoProcessingService
from app.services.upload_service import UploadService
from app.services.chat_service import ChatService


@lru_cache
def get_storage_service() -> StorageService:
    return StorageService()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@lru_cache
def get_pinecone_service() -> PineconeService:
    return PineconeService()


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache
def get_document_service() -> DocumentProcessingService:
    return DocumentProcessingService()


@lru_cache
def get_video_service() -> VideoProcessingService:
    return VideoProcessingService()


@lru_cache
def get_upload_service() -> UploadService:
    return UploadService(
        storage=get_storage_service(),
        embedding=get_embedding_service(),
        pinecone=get_pinecone_service(),
        document_proc=get_document_service(),
        video_proc=get_video_service(),
    )


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(
        storage=get_storage_service(),
        embedding=get_embedding_service(),
        pinecone=get_pinecone_service(),
        llm=get_llm_service(),
        document_proc=get_document_service(),
        video_proc=get_video_service(),
    )

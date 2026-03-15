from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# --- Upload SSE Progress Events ---
class UploadProgressEvent(BaseModel):
    type: Literal["progress"] = "progress"
    percent: int
    status: str  # "uploading" | "processing" | "indexing"


class UploadDoneEvent(BaseModel):
    type: Literal["done"] = "done"
    file_id: str
    filename: str
    indexed_at: str


class UploadErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


# --- Files ---
class IndexedFile(BaseModel):
    file_id: str
    filename: str
    type: Literal["image", "video", "document"]
    indexed_at: str


# --- Search ---
class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    media_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class SearchResult(BaseModel):
    id: str
    type: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int


# --- Chat Sources (typed) ---
class ImageSource(BaseModel):
    id: str
    filename: str
    thumbnail_path: str
    score: float


class VideoSource(BaseModel):
    id: str
    filename: str
    timestamp_sec: float
    score: float


class DocumentSource(BaseModel):
    id: str
    filename: str
    excerpt: str
    page: Optional[int] = None
    score: float


class Sources(BaseModel):
    images: List[ImageSource] = []
    videos: List[VideoSource] = []
    documents: List[DocumentSource] = []


# --- Chat Stream Events ---
class TextChunkEvent(BaseModel):
    type: Literal["text_chunk"] = "text_chunk"
    content: str


class SourcesEvent(BaseModel):
    type: Literal["sources"] = "sources"
    data: Sources


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


# --- Answer (non-streaming, used by /api/search/answer) ---
class AnswerRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    media_types: Optional[List[str]] = None


class AnswerResponse(BaseModel):
    answer: str
    sources: Sources
    query: str
    generated_at: datetime

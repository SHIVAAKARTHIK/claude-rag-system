import tempfile
import os
from typing import AsyncGenerator, Optional

from fastapi import UploadFile

from app.models.schemas import (
    TextChunkEvent,
    SourcesEvent,
    ErrorEvent,
    Sources,
    ImageSource,
    VideoSource,
    DocumentSource,
)
from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.services.llm_service import LLMService
from app.services.document_processing import DocumentProcessingService
from app.services.video_processing import VideoProcessingService


class ChatService:
    def __init__(
        self,
        storage: StorageService,
        embedding: EmbeddingService,
        pinecone: PineconeService,
        llm: LLMService,
        document_proc: DocumentProcessingService,
        video_proc: VideoProcessingService,
    ):
        self.storage = storage
        self.embedding = embedding
        self.pinecone = pinecone
        self.llm = llm
        self.document_proc = document_proc
        self.video_proc = video_proc

    async def handle_chat(
        self,
        message: str,
        query_image: Optional[UploadFile] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Main chat handler — yields SSE-formatted strings.
        query_image triggers visual similarity search (CLIP/vision embedding).
        message alone triggers text similarity search.
        NOTE: query_image is NOT indexed into Pinecone.
        """
        # Phase 1: Get query embedding
        try:
            if query_image:
                image_bytes = await query_image.read()
                # Write to temp file for embed_image (needs a path)
                ext = os.path.splitext(query_image.filename or "img")[1] or ".jpg"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                try:
                    query_embedding, _ = await self.embedding.embed_image(tmp_path)
                finally:
                    os.unlink(tmp_path)
            else:
                query_embedding = await self.embedding.embed_text(message)
        except Exception as e:
            yield f"data: {ErrorEvent(message=f'Embedding error: {str(e)}').model_dump_json()}\n\n"
            return

        # Phase 2: Search Pinecone
        try:
            raw_results = await self.pinecone.query(query_embedding, top_k=10)
        except Exception:
            raw_results = []

        # Phase 3: Stream GPT-4 answer
        context = self.llm.format_context(raw_results)
        try:
            async for chunk in self.llm.stream_answer(message, context):
                yield f"data: {TextChunkEvent(content=chunk).model_dump_json()}\n\n"
        except Exception as e:
            yield f"data: {ErrorEvent(message=f'LLM error: {str(e)}').model_dump_json()}\n\n"
            return

        # Phase 4: Yield typed sources
        sources = self._build_typed_sources(raw_results)
        yield f"data: {SourcesEvent(data=sources).model_dump_json()}\n\n"

    RELEVANCE_THRESHOLD = 0.35  # cosine similarity — below this is not relevant

    def _build_typed_sources(self, results: list[dict]) -> Sources:
        images, videos, documents = [], [], []
        seen_files: set[str] = set()

        # Always include the top result if it exists; filter the rest by threshold
        for i, r in enumerate(results):
            meta = r.get("metadata", {})
            score = r.get("score", 0.0)

            # Always show the top match; skip the rest if below threshold
            if i > 0 and score < self.RELEVANCE_THRESHOLD:
                continue

            r_type = meta.get("type", "")
            file_id = meta.get("file_id", r["id"])

            if r_type == "image" and file_id not in seen_files:
                seen_files.add(file_id)
                images.append(ImageSource(
                    id=file_id,
                    filename=meta.get("filename", ""),
                    thumbnail_path=meta.get("thumbnail_path", ""),
                    score=score,
                ))

            elif r_type == "video_frame":
                key = f"{file_id}_{meta.get('timestamp_sec', 0)}"
                if key not in seen_files:
                    seen_files.add(key)
                    videos.append(VideoSource(
                        id=file_id,
                        filename=meta.get("filename", ""),
                        timestamp_sec=meta.get("timestamp_sec", 0.0),
                        score=score,
                    ))

            elif r_type == "document_chunk":
                key = f"{file_id}_{meta.get('chunk_index', 0)}"
                if key not in seen_files:
                    seen_files.add(key)
                    documents.append(DocumentSource(
                        id=file_id,
                        filename=meta.get("filename", ""),
                        excerpt=meta.get("text", "")[:200],
                        page=meta.get("page"),
                        score=score,
                    ))

        return Sources(images=images, videos=videos, documents=documents)

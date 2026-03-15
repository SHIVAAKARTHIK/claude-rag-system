import json
from datetime import datetime
from typing import AsyncGenerator, Literal

from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.services.document_processing import DocumentProcessingService
from app.services.video_processing import VideoProcessingService


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def progress_event(percent: int, status: str) -> str:
    return _sse({"type": "progress", "percent": percent, "status": status})


class UploadService:
    def __init__(
        self,
        storage: StorageService,
        embedding: EmbeddingService,
        pinecone: PineconeService,
        document_proc: DocumentProcessingService,
        video_proc: VideoProcessingService,
    ):
        self.storage = storage
        self.embedding = embedding
        self.pinecone = pinecone
        self.document_proc = document_proc
        self.video_proc = video_proc

    async def handle_upload(
        self,
        file_data: bytes,
        filename: str,
        media_type: Literal["image", "video", "document"],
    ) -> AsyncGenerator[str, None]:
        """Handles indexing of a file into the knowledge base. Yields SSE progress events."""
        from uuid import uuid4
        file_id = str(uuid4())

        try:
            yield progress_event(10, "uploading")

            # Save to .tmp/uploads/
            file_path = await self.storage.save(file_data, file_id, filename)

            yield progress_event(30, "processing")

            if media_type == "image":
                thumbnail_path = await self.storage.make_thumbnail(file_path, file_id)
                embedding, description = await self.embedding.embed_image(str(file_path))
                vectors = [{
                    "id": file_id,
                    "values": embedding,
                    "metadata": {
                        "type": "image",
                        "file_id": file_id,
                        "filename": filename,
                        "path": str(file_path),
                        "thumbnail_path": thumbnail_path,
                        "description": description,
                    },
                }]

            elif media_type == "video":
                frames = self.video_proc.extract_frames(str(file_path), file_id)
                vectors = []
                for frame in frames:
                    emb, description = await self.embedding.embed_image(frame["frame_path"])
                    vectors.append({
                        "id": f"{file_id}_frame_{frame['frame_id']}",
                        "values": emb,
                        "metadata": {
                            "type": "video_frame",
                            "file_id": file_id,
                            "filename": filename,
                            "frame_path": frame["frame_path"],
                            "frame_url": frame["frame_url"],
                            "timestamp_sec": frame["timestamp_sec"],
                            "description": description,
                        },
                    })

            else:  # document
                chunks = self.document_proc.process_file(str(file_path), filename)
                if not chunks:
                    raise ValueError("No text could be extracted from the document")
                texts = [c["text"] for c in chunks]
                embeddings = await self.embedding.embed_texts_batch(texts)
                vectors = []
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                    vectors.append({
                        "id": f"{file_id}_chunk_{i}",
                        "values": emb,
                        "metadata": {
                            "type": "document_chunk",
                            "file_id": file_id,
                            "filename": filename,
                            "text": chunk["text"][:500],
                            "excerpt": chunk["text"][:200],
                            "page": chunk.get("page"),
                            "chunk_index": i,
                        },
                    })

            yield progress_event(80, "indexing")
            await self.pinecone.upsert(vectors)

            # Save metadata for /api/files listing
            await self.storage.save_metadata(file_id, filename, media_type)

            yield _sse({
                "type": "done",
                "file_id": file_id,
                "filename": filename,
                "indexed_at": datetime.utcnow().isoformat() + "Z",
            })

        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})

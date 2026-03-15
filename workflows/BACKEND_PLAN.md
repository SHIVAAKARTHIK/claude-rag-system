# Backend Architecture Plan - Multimodal RAG Chatbot

## Objective
Build an async FastAPI backend with two distinct flows:
1. **Index Flow** — Users upload files (PDF, MD, PNG, JPEG, MP4) via dedicated upload endpoints. Files are stored in `.tmp/uploads/`, processed, embedded, and indexed into Pinecone. Upload progress is streamed back via SSE.
2. **Chat Flow** — Users send a text message (and optionally a query image for visual similarity search) to `/api/chat`. The backend searches Pinecone, generates a streaming GPT-4 answer, and returns typed sources.

---

## Architecture Overview

### Two Independent Flows
```
INDEX FLOW                            CHAT FLOW
──────────────────────────            ──────────────────────────────────────
POST /api/upload/{type}               POST /api/chat
       ↓                                     ↓
  StorageService                        ChatService
  (.tmp/uploads/)                       ├── if query_image: EmbeddingService (CLIP)
       ↓                                ├── else: EmbeddingService (text)
  [image] → EmbeddingService (CLIP)     ├── PineconeService (search top-k)
  [video] → VideoProcessingService      └── LLMService (stream GPT-4 answer)
            → EmbeddingService (CLIP)          ↓
  [document] → DocumentProcessingService  Server-Sent Events → frontend
               → EmbeddingService (text)
       ↓
  PineconeService (upsert vectors)
       ↓
  SSE progress events → frontend
```

### Core Services

**1. StorageService** (`services/storage_service.py`)
- Save uploaded files to `.tmp/uploads/`
- Save video frames to `.tmp/uploads/frames/`
- Save image thumbnails to `.tmp/uploads/thumbnails/`
- Generate UUID-based file IDs
- Store metadata as JSON in `.tmp/uploads/metadata/`

**2. EmbeddingService** (`services/embedding_service.py`)
- Text embeddings: `text-embedding-3-large` (1536 dims)
- Image embeddings: CLIP via OpenAI Vision API
- Batch processing with exponential backoff retry
- Used for both indexing and query-time embedding

**3. PineconeService** (`services/pinecone_service.py`)
- Initialize and manage Pinecone index
- Upsert vectors with metadata (type, filename, path, timestamp, thumbnail_path)
- Query vectors with optional type filters
- Return typed results (image / video_frame / document_chunk)
- Delete vectors by file_id (namespace or metadata filter)

**4. LLMService** (`services/llm_service.py`)
- Stream GPT-4 responses with retrieved context
- Format system prompt + context from search results
- Handle token limits (truncate context if needed)

**5. VideoProcessingService** (`services/video_processing.py`)
- Extract up to 10 key frames using scene detection (scenedetect + opencv)
- Save frames to `.tmp/uploads/frames/{file_id}/`
- Return frame paths + timestamps for embedding

**6. DocumentProcessingService** (`services/document_processing.py`)
- Parse PDF (pypdf), Markdown (.md as plain text)
- Chunk into 500-token segments with 50-token overlap
- Return chunks with page numbers / line ranges

**7. ChatService** (`services/chat_service.py`)
- Orchestrates the full chat flow
- If `query_image` present: embed with CLIP, search by image similarity
- Else: embed `message` with text embeddings, search by text similarity
- Streams GPT-4 answer
- Yields typed sources at the end

---

## API Routes

### Upload Endpoints (`api/upload.py`) — SSE streaming progress

**POST /api/upload/image** — PNG, JPEG/JPG — Max 10MB
**POST /api/upload/video** — MP4 — Max 100MB
**POST /api/upload/document** — PDF, MD — Max 50MB

All accept `multipart/form-data` with a single `file` field.

All return `text/event-stream` with progress events:

```
# Uploading to disk
data: {"type": "progress", "percent": 10, "status": "uploading"}

# Processing (embedding / frame extraction / chunking)
data: {"type": "progress", "percent": 40, "status": "processing"}

# Indexing into Pinecone
data: {"type": "progress", "percent": 80, "status": "indexing"}

# Done
data: {"type": "done", "file_id": "uuid", "filename": "beach.jpg", "indexed_at": "2026-03-15T10:00:00Z"}

# On error
data: {"type": "error", "message": "File too large"}
```

**Implementation:**
```python
@router.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    return StreamingResponse(
        upload_service.handle_upload(file, media_type="image"),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

---

### Files Endpoint (`api/files.py`) — NEW

**GET /api/files** — Returns list of all indexed files
```json
[
  {"file_id": "uuid", "filename": "beach.jpg", "type": "image", "indexed_at": "2026-03-15T10:00:00Z"},
  {"file_id": "uuid", "filename": "report.pdf", "type": "document", "indexed_at": "2026-03-15T10:05:00Z"}
]
```

**DELETE /api/delete/{file_id}** — Removes from Pinecone + `.tmp/uploads/`
```json
{"status": "deleted", "file_id": "uuid"}
```

---

### Chat Endpoint (`api/chat.py`)

**POST /api/chat**
- Request: `multipart/form-data`
  - `message: str` — user's text question
  - `query_image: UploadFile` (optional) — image to find visually similar content

- Response: `text/event-stream` (SSE)

**Stream event sequence:**
```
# If query_image was provided, skip text search, do visual search
# (no upload_progress events — the query image is NOT indexed)

# Phase 1 — stream GPT-4 answer chunks
data: {"type": "text_chunk", "content": "The most similar images show "}
data: {"type": "text_chunk", "content": "tropical beach scenes..."}

# Phase 2 — final sources (one event, after streaming completes)
data: {"type": "sources", "data": {
  "images": [
    {"id": "uuid", "filename": "beach.jpg", "thumbnail_path": "/.tmp/uploads/thumbnails/uuid_thumb.jpg", "score": 0.92}
  ],
  "videos": [
    {"id": "uuid", "filename": "sunset.mp4", "timestamp_sec": 23.5, "score": 0.87}
  ],
  "documents": [
    {"id": "uuid", "filename": "report.pdf", "excerpt": "The beach area...", "page": 3, "score": 0.81}
  ]
}}
```

**Implementation:**
```python
@router.post("/api/chat")
async def chat(
    message: str = Form(...),
    query_image: Optional[UploadFile] = File(default=None)
):
    return StreamingResponse(
        chat_service.handle_chat(message, query_image),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

---

### Search Endpoints (`api/search.py`)

**POST /api/search/text** — `{"query": "...", "top_k": 10, "media_types": [...]}`
**POST /api/search/image** — multipart with query image (visual similarity)
**POST /api/search/hybrid** — `{"query": "...", "keywords": [...], "top_k": 10}`

---

### Utility Endpoints (`api/health.py`)

**GET /api/health** — `{"status": "healthy", "services": {"pinecone": "ok", "openai": "ok"}}`
**GET /api/stats** — `{"total_items": 1523, "images": 892, "videos": 45, "documents": 586}`

---

## ChatService (`services/chat_service.py`)

```python
async def handle_chat(
    message: str,
    query_image: Optional[UploadFile]
) -> AsyncGenerator[str, None]:
    """
    Main chat handler — yields SSE-formatted strings.
    query_image triggers visual similarity search (CLIP embedding).
    message alone triggers text similarity search.
    NOTE: query_image is NOT indexed into Pinecone.
    """
    # Phase 1: Get query embedding
    if query_image:
        image_bytes = await query_image.read()
        query_embedding = await embedding_service.embed_image_bytes(image_bytes)
    else:
        query_embedding = await embedding_service.embed_text(message)

    # Phase 2: Search Pinecone
    raw_results = await pinecone_service.query(query_embedding, top_k=10)

    # Phase 3: Stream GPT-4 answer
    context = format_context(raw_results)
    async for chunk in llm_service.stream_answer(message, context):
        yield f"data: {TextChunkEvent(type='text_chunk', content=chunk).model_dump_json()}\n\n"

    # Phase 4: Yield typed sources
    sources = build_typed_sources(raw_results)
    yield f"data: {SourcesEvent(type='sources', data=sources).model_dump_json()}\n\n"
```

---

## Upload Service (`services/upload_service.py`)

```python
async def handle_upload(
    file: UploadFile,
    media_type: Literal["image", "video", "document"]
) -> AsyncGenerator[str, None]:
    """
    Handles indexing of a file into the knowledge base.
    Yields SSE progress events.
    """
    file_id = str(uuid4())

    yield progress_event(10, "uploading")

    # Save to .tmp/uploads/
    file_path = await storage_service.save(file, file_id)

    yield progress_event(30, "processing")

    if media_type == "image":
        thumbnail = await storage_service.make_thumbnail(file_path, file_id)
        embedding = await embedding_service.embed_image_file(file_path)
        vectors = [{"id": file_id, "values": embedding, "metadata": {
            "type": "image", "filename": file.filename,
            "path": str(file_path), "thumbnail_path": str(thumbnail),
            "file_id": file_id
        }}]

    elif media_type == "video":
        frames = await video_service.extract_frames(file_path, file_id)
        vectors = []
        for frame in frames:
            emb = await embedding_service.embed_image_file(frame.path)
            vectors.append({"id": f"{file_id}_f{frame.index}", "values": emb, "metadata": {
                "type": "video_frame", "filename": file.filename,
                "frame_path": str(frame.path), "timestamp_sec": frame.timestamp,
                "file_id": file_id
            }})

    else:  # document
        chunks = await document_service.parse_and_chunk(file_path)
        vectors = []
        for i, chunk in enumerate(chunks):
            emb = await embedding_service.embed_text(chunk.text)
            vectors.append({"id": f"{file_id}_c{i}", "values": emb, "metadata": {
                "type": "document_chunk", "filename": file.filename,
                "excerpt": chunk.text[:200], "page": chunk.page,
                "file_id": file_id
            }})

    yield progress_event(80, "indexing")
    await pinecone_service.upsert(vectors)

    # Save metadata for /api/files listing
    await storage_service.save_metadata(file_id, file.filename, media_type)

    yield f"data: {json.dumps({'type': 'done', 'file_id': file_id, 'filename': file.filename, 'indexed_at': datetime.utcnow().isoformat()})}\n\n"


def progress_event(percent: int, status: str) -> str:
    return f"data: {json.dumps({'type': 'progress', 'percent': percent, 'status': status})}\n\n"
```

---

## Data Models (`models/schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# --- Upload Progress Events ---
class UploadProgressEvent(BaseModel):
    type: Literal["progress"]
    percent: int
    status: str  # "uploading" | "processing" | "indexing"

class UploadDoneEvent(BaseModel):
    type: Literal["done"]
    file_id: str
    filename: str
    indexed_at: str

class UploadErrorEvent(BaseModel):
    type: Literal["error"]
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
    type: Literal["image", "video_frame", "document_chunk"]
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
    type: Literal["text_chunk"]
    content: str

class SourcesEvent(BaseModel):
    type: Literal["sources"]
    data: Sources

class ErrorEvent(BaseModel):
    type: Literal["error"]
    message: str
```

---

## Configuration (`core/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "multimodal-rag"
    PINECONE_DIMENSION: int = 1536

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_CHAT_MODEL: str = "gpt-4"

    # Storage — all files go into .tmp/uploads/
    UPLOAD_DIR: str = "./.tmp/uploads"
    FRAMES_DIR: str = "./.tmp/uploads/frames"
    THUMBNAILS_DIR: str = "./.tmp/uploads/thumbnails"
    METADATA_DIR: str = "./.tmp/uploads/metadata"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Processing
    VIDEO_MAX_FRAMES: int = 10
    DOCUMENT_CHUNK_SIZE: int = 500
    DOCUMENT_CHUNK_OVERLAP: int = 50
    SEARCH_TOP_K: int = 10

    # API
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Error Handling

**Retry Logic:**
- OpenAI API: 3 retries, exponential backoff (2s, 4s, 8s) via `tenacity`
- Pinecone: 2 retries, 1s delay
- File ops: yield error SSE event, do not crash the server

**CORS:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Static file serving for thumbnails/frames:**
```python
app.mount("/.tmp/uploads", StaticFiles(directory=".tmp/uploads"), name="uploads")
```
This lets the frontend `<img src="/.tmp/uploads/thumbnails/uuid_thumb.jpg" />` work directly.

---

## Dependencies (`requirements.txt`)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
pinecone-client==3.0.0
openai==1.10.0
python-dotenv==1.0.0
opencv-python==4.9.0.80
scenedetect[opencv]==0.6.3
pypdf==4.0.0
python-magic==0.4.27
pillow==10.2.0
aiofiles==23.2.1
httpx==0.26.0
tenacity==8.2.3
```

---

## Folder Structure (`.tmp/uploads/`)

```
.tmp/uploads/
├── {file_id}.jpg              ← original image
├── {file_id}.pdf              ← original document
├── {file_id}.mp4              ← original video
├── thumbnails/
│   └── {file_id}_thumb.jpg   ← resized thumbnail (max 256×256)
├── frames/
│   └── {file_id}/
│       ├── frame_0001.jpg    ← extracted video frame
│       └── frame_0002.jpg
└── metadata/
    └── {file_id}.json        ← {file_id, filename, type, indexed_at}
```

---

## Start Here
1. Set up virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install: `pip install -r requirements.txt`
3. Create `.env` with API keys
4. Create `.tmp/uploads/` directories: `mkdir -p .tmp/uploads/{thumbnails,frames,metadata}`
5. Run `tools/pinecone_init.py` to initialize the Pinecone index
6. Implement services in order:
   `StorageService` → `EmbeddingService` → `PineconeService` → `DocumentProcessingService` → `VideoProcessingService` → `UploadService` → `LLMService` → `ChatService`
7. Wire up routes: `api/upload.py` → `api/files.py` → `api/chat.py` → `api/search.py` → `api/health.py`
8. Start server: `uvicorn app.main:app --reload`
9. Test upload SSE with curl: `curl -X POST http://localhost:8000/api/upload/image -F "file=@test.jpg" --no-buffer`
10. Test chat with curl: `curl -X POST http://localhost:8000/api/chat -F "message=what do you see?" --no-buffer`

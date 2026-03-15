from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_upload_service, get_storage_service
from app.models.schemas import IndexedFile
from app.services.upload_service import UploadService
from app.services.storage_service import StorageService

router = APIRouter()

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

MAX_IMAGE = 10 * 1024 * 1024    # 10 MB
MAX_VIDEO = 100 * 1024 * 1024   # 100 MB
MAX_DOC = 50 * 1024 * 1024      # 50 MB


@router.post("/api/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service),
):
    # Read bytes eagerly — UploadFile is closed before StreamingResponse generator runs
    data = await file.read()
    if len(data) > MAX_IMAGE:
        raise HTTPException(413, "Image exceeds 10 MB limit")
    filename = file.filename or "image.jpg"
    return StreamingResponse(
        upload_service.handle_upload(data, filename, media_type="image"),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/api/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service),
):
    data = await file.read()
    if len(data) > MAX_VIDEO:
        raise HTTPException(413, "Video exceeds 100 MB limit")
    filename = file.filename or "video.mp4"
    return StreamingResponse(
        upload_service.handle_upload(data, filename, media_type="video"),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/api/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service),
):
    data = await file.read()
    if len(data) > MAX_DOC:
        raise HTTPException(413, "Document exceeds 50 MB limit")
    filename = file.filename or "document.pdf"
    return StreamingResponse(
        upload_service.handle_upload(data, filename, media_type="document"),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


# --- File listing / management ---

@router.get("/api/files", response_model=list[IndexedFile])
async def list_files(storage: StorageService = Depends(get_storage_service)):
    return [IndexedFile(**r) for r in storage.list_all_files()]


@router.get("/api/files/{file_id}", response_model=IndexedFile)
async def get_file(file_id: str, storage: StorageService = Depends(get_storage_service)):
    record = storage.get_file_metadata(file_id)
    if not record:
        raise HTTPException(404, f"File {file_id} not found")
    return IndexedFile(**record)

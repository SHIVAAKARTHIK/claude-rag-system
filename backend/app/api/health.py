from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_pinecone_service, get_storage_service
from app.services.pinecone_service import PineconeService
from app.services.storage_service import StorageService

router = APIRouter()


@router.get("/api/health")
async def health_check(
    pinecone: PineconeService = Depends(get_pinecone_service),
):
    pinecone_status = "ok"
    try:
        pinecone.get_stats()
    except Exception as e:
        pinecone_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "services": {
            "pinecone": pinecone_status,
            "openai": "ok",  # validated at startup via config
        },
    }


@router.get("/api/stats")
async def get_stats(
    storage: StorageService = Depends(get_storage_service),
    pinecone: PineconeService = Depends(get_pinecone_service),
):
    counts = storage.get_total_counts()
    try:
        pinecone_stats = pinecone.get_stats()
        vector_count = pinecone_stats.get("total_vector_count", 0)
    except Exception:
        vector_count = 0

    return {
        "total_items": counts["total"],
        "images": counts["images"],
        "videos": counts["videos"],
        "documents": counts["documents"],
        "total_vectors": vector_count,
    }


@router.delete("/api/delete/{file_id}")
async def delete_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service),
    pinecone: PineconeService = Depends(get_pinecone_service),
):
    meta = storage.get_file_metadata(file_id)
    if not meta:
        raise HTTPException(404, f"File {file_id} not found")

    # Delete all vectors for this file (main + chunks/frames)
    try:
        # Delete by file_id prefix - delete the main vector + prefixed ones
        ids_to_delete = [file_id]
        # Attempt to find and delete chunk/frame vectors via listing if supported
        try:
            for i in range(200):  # delete up to 200 chunks/frames
                ids_to_delete.append(f"{file_id}_chunk_{i}")
                ids_to_delete.append(f"{file_id}_frame_{i}")
        except Exception:
            pass
        await pinecone.delete(ids_to_delete)
    except Exception:
        pass

    deleted = storage.delete_file(file_id)
    if not deleted:
        raise HTTPException(500, "Failed to delete file from storage")

    return {"status": "deleted", "file_id": file_id}

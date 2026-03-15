from datetime import datetime
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends

from app.core.dependencies import get_embedding_service, get_llm_service, get_pinecone_service
from app.models.schemas import (
    AnswerRequest,
    AnswerResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    Sources,
)
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.pinecone_service import PineconeService

router = APIRouter()


def _build_type_filter(media_types: list[str] | None) -> dict | None:
    if not media_types:
        return None
    type_map = {
        "image": "image",
        "video": "video_frame",
        "document": "document_chunk",
    }
    mapped = [type_map.get(t, t) for t in media_types]
    return {"type": {"$in": mapped}}


@router.post("/api/search/text", response_model=SearchResponse)
async def search_text(
    request: SearchRequest,
    embedding: EmbeddingService = Depends(get_embedding_service),
    pinecone: PineconeService = Depends(get_pinecone_service),
):
    query_emb = await embedding.embed_text(request.query)
    filter_dict = _build_type_filter(request.media_types)
    results = await pinecone.query(query_emb, top_k=request.top_k, filter=filter_dict)
    return SearchResponse(
        results=[SearchResult(id=r["id"], type=r["metadata"].get("type", "unknown"), score=r["score"], metadata=r["metadata"]) for r in results],
        query=request.query,
        total_results=len(results),
    )


@router.post("/api/search/image", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    top_k: int = 10,
    embedding: EmbeddingService = Depends(get_embedding_service),
    pinecone: PineconeService = Depends(get_pinecone_service),
):
    import tempfile, os
    data = await file.read()
    suffix = os.path.splitext(file.filename or "img")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        emb, _ = await embedding.embed_image(tmp_path)
    finally:
        os.unlink(tmp_path)

    results = await pinecone.query(emb, top_k=top_k)
    return SearchResponse(
        results=[SearchResult(id=r["id"], type=r["metadata"].get("type", "unknown"), score=r["score"], metadata=r["metadata"]) for r in results],
        query=f"image:{file.filename}",
        total_results=len(results),
    )


@router.post("/api/search/hybrid", response_model=SearchResponse)
async def search_hybrid(
    request: SearchRequest,
    embedding: EmbeddingService = Depends(get_embedding_service),
    pinecone: PineconeService = Depends(get_pinecone_service),
):
    # Enhance query with keywords for better semantic coverage
    query_text = request.query
    if request.keywords:
        query_text = f"{query_text} {' '.join(request.keywords)}"

    query_emb = await embedding.embed_text(query_text)
    filter_dict = _build_type_filter(request.media_types)
    results = await pinecone.query(query_emb, top_k=request.top_k, filter=filter_dict)
    return SearchResponse(
        results=[SearchResult(id=r["id"], type=r["metadata"].get("type", "unknown"), score=r["score"], metadata=r["metadata"]) for r in results],
        query=query_text,
        total_results=len(results),
    )


@router.post("/api/search/answer", response_model=AnswerResponse)
async def search_and_answer(
    request: AnswerRequest,
    embedding: EmbeddingService = Depends(get_embedding_service),
    pinecone: PineconeService = Depends(get_pinecone_service),
    llm: LLMService = Depends(get_llm_service),
):
    query_emb = await embedding.embed_text(request.query)
    filter_dict = _build_type_filter(request.media_types)
    results = await pinecone.query(query_emb, top_k=request.top_k, filter=filter_dict)

    context = llm.format_context(results)
    full_answer = ""
    async for chunk in llm.stream_answer(request.query, context):
        full_answer += chunk

    # Build typed sources
    from app.services.chat_service import ChatService
    images, videos, documents = [], [], []
    seen: set[str] = set()
    for r in results:
        meta = r.get("metadata", {})
        score = r.get("score", 0.0)
        r_type = meta.get("type", "")
        fid = meta.get("file_id", r["id"])
        if r_type == "image" and fid not in seen:
            seen.add(fid)
            from app.models.schemas import ImageSource
            images.append(ImageSource(id=fid, filename=meta.get("filename", ""), thumbnail_path=meta.get("thumbnail_path", ""), score=score))
        elif r_type == "video_frame":
            key = f"{fid}_{meta.get('timestamp_sec', 0)}"
            if key not in seen:
                seen.add(key)
                from app.models.schemas import VideoSource
                videos.append(VideoSource(id=fid, filename=meta.get("filename", ""), timestamp_sec=meta.get("timestamp_sec", 0.0), score=score))
        elif r_type == "document_chunk":
            key = f"{fid}_{meta.get('chunk_index', 0)}"
            if key not in seen:
                seen.add(key)
                from app.models.schemas import DocumentSource
                documents.append(DocumentSource(id=fid, filename=meta.get("filename", ""), excerpt=meta.get("text", "")[:200], page=meta.get("page"), score=score))

    return AnswerResponse(
        answer=full_answer,
        sources=Sources(images=images, videos=videos, documents=documents),
        query=request.query,
        generated_at=datetime.utcnow(),
    )

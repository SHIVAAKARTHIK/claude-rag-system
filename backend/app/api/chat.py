from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/api/chat")
async def chat(
    message: str = Form(...),
    query_image: Optional[UploadFile] = File(default=None),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Stream a GPT-4 answer via SSE.
    - message: user's text question
    - query_image (optional): triggers visual similarity search instead of text search
    """
    return StreamingResponse(
        chat_service.handle_chat(message, query_image),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )

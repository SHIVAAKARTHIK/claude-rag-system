from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api import chat, upload, search, health

app = FastAPI(title="Multimodal RAG API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploads directory as static assets (thumbnails, frames, originals)
# URL path mirrors the UPLOAD_DIR path, e.g. /data/uploads/thumbnails/xxx.jpg
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
# Mount at the URL path that matches the stored thumbnail/frame URLs
mount_path = "/" + str(upload_dir).replace("\\", "/").lstrip("./")
app.mount(mount_path, StaticFiles(directory=str(upload_dir)), name="uploads")

# Routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {"message": "Multimodal RAG API is running", "docs": "/docs"}

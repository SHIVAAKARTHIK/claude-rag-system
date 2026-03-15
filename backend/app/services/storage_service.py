import uuid
import json
import aiofiles
from datetime import datetime
from pathlib import Path
from PIL import Image
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.frames_dir = Path(settings.FRAMES_DIR)
        self.thumbnails_dir = Path(settings.THUMBNAILS_DIR)
        self.metadata_dir = Path(settings.METADATA_DIR)

        for d in (self.upload_dir, self.frames_dir, self.thumbnails_dir, self.metadata_dir):
            d.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self) -> str:
        return str(uuid.uuid4())

    async def save(self, file_data: bytes, file_id: str, filename: str) -> Path:
        """Save raw bytes to .tmp/uploads/{file_id}{ext} and return the path."""
        ext = Path(filename).suffix.lower() or ".bin"
        saved_path = self.upload_dir / f"{file_id}{ext}"
        async with aiofiles.open(saved_path, "wb") as f:
            await f.write(file_data)
        return saved_path

    async def make_thumbnail(self, image_path: Path, file_id: str) -> str:
        """Resize image to max 256×256, save to thumbnails dir. Returns URL path."""
        thumb_path = self.thumbnails_dir / f"{file_id}_thumb.jpg"
        # URL path mirrors the filesystem path relative to the static mount root
        # Static mount: /data/uploads → ./data/uploads
        thumb_url = "/" + str(thumb_path).replace("\\", "/").lstrip("./")
        try:
            img = Image.open(image_path).convert("RGB")
            img.thumbnail((256, 256))
            img.save(thumb_path, "JPEG")
            return thumb_url
        except Exception:
            # Fall back: serve the original image
            orig_url = "/" + str(image_path).replace("\\", "/").lstrip("./")
            return orig_url

    async def save_metadata(self, file_id: str, filename: str, media_type: str):
        """Persist {file_id, filename, type, indexed_at} JSON for /api/files listing."""
        metadata = {
            "file_id": file_id,
            "filename": filename,
            "type": media_type,
            "indexed_at": datetime.utcnow().isoformat() + "Z",
        }
        meta_path = self.metadata_dir / f"{file_id}.json"
        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2))

    async def update_metadata(self, file_id: str, updates: dict):
        meta = self.get_file_metadata(file_id) or {}
        meta.update(updates)
        meta_path = self.metadata_dir / f"{file_id}.json"
        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(meta, indent=2))

    def get_file_metadata(self, file_id: str) -> dict | None:
        meta_path = self.metadata_dir / f"{file_id}.json"
        if not meta_path.exists():
            return None
        with open(meta_path) as f:
            return json.load(f)

    def list_all_files(self) -> list[dict]:
        records = []
        for meta_file in self.metadata_dir.glob("*.json"):
            try:
                with open(meta_file) as f:
                    records.append(json.load(f))
            except Exception:
                continue
        return sorted(records, key=lambda x: x.get("indexed_at", ""), reverse=True)

    def delete_file(self, file_id: str) -> bool:
        meta = self.get_file_metadata(file_id)
        if not meta:
            return False

        # Remove original file
        for candidate in self.upload_dir.glob(f"{file_id}.*"):
            candidate.unlink(missing_ok=True)

        # Remove thumbnail
        thumb = self.thumbnails_dir / f"{file_id}_thumb.jpg"
        thumb.unlink(missing_ok=True)

        # Remove frame dir
        frame_dir = self.frames_dir / file_id
        if frame_dir.exists():
            import shutil
            shutil.rmtree(frame_dir, ignore_errors=True)

        # Remove metadata
        (self.metadata_dir / f"{file_id}.json").unlink(missing_ok=True)
        return True

    def get_total_counts(self) -> dict:
        records = self.list_all_files()
        counts = {"total": len(records), "images": 0, "videos": 0, "documents": 0}
        for r in records:
            t = r.get("type", "")
            if t in counts:
                counts[t] += 1
        return counts

import cv2
import uuid
from pathlib import Path
from app.core.config import settings


class VideoProcessingService:
    def __init__(self):
        self.frames_dir = Path(settings.FRAMES_DIR)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.max_frames = settings.VIDEO_MAX_FRAMES

    def extract_frames(self, video_path: str, video_id: str) -> list[dict]:
        """Extract up to max_frames evenly-spaced key frames from a video."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        if total_frames <= 0:
            cap.release()
            raise ValueError("Video has no frames")

        # Pick evenly spaced frame indices (skip first and last 5% to avoid fade-in/out)
        margin = max(1, int(total_frames * 0.05))
        usable_start = margin
        usable_end = total_frames - margin
        usable_range = max(1, usable_end - usable_start)

        num_frames = min(self.max_frames, total_frames)
        if num_frames <= 1:
            frame_indices = [total_frames // 2]
        else:
            step = usable_range / (num_frames - 1)
            frame_indices = [int(usable_start + i * step) for i in range(num_frames)]

        # Save frames into .tmp/uploads/frames/{video_id}/
        video_frames_dir = self.frames_dir / video_id
        video_frames_dir.mkdir(parents=True, exist_ok=True)

        extracted = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            timestamp_sec = idx / fps
            frame_id = str(uuid.uuid4())
            frame_filename = f"frame_{frame_id}.jpg"
            frame_path = video_frames_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)

            frame_url = "/" + str(frame_path).replace("\\", "/").lstrip("./")
            extracted.append({
                "frame_id": frame_id,
                "frame_path": str(frame_path),
                "frame_url": frame_url,
                "timestamp_sec": round(timestamp_sec, 2),
                "frame_index": idx,
            })

        cap.release()
        return extracted

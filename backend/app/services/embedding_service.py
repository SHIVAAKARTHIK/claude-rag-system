import base64
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.chat_model = settings.OPENAI_CHAT_MODEL

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def embed_text(self, text: str) -> list[float]:
        text = text[:8000]  # stay within token limits
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def embed_texts_batch(self, texts: list[str]) -> list[list[float]]:
        truncated = [t[:8000] for t in texts]
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=truncated,
        )
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def embed_image(self, image_path: str) -> tuple[list[float], str]:
        """Describe image with vision then embed the description. Returns (embedding, description)."""
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lower().lstrip(".")
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/jpeg")

        vision_response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                        },
                        {
                            "type": "text",
                            "text": "Describe this image in detail for semantic search indexing. Include objects, colors, scenes, actions, and any text visible.",
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        description = vision_response.choices[0].message.content or ""
        embedding = await self.embed_text(description)
        return embedding, description

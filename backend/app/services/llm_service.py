from typing import AsyncGenerator
from openai import AsyncOpenAI
from app.core.config import settings

MAX_CONTEXT_CHARS = 6000


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_CHAT_MODEL

    async def stream_answer(
        self,
        message: str,
        context: str,
    ) -> AsyncGenerator[str, None]:
        system_prompt = (
            "You are a helpful assistant for a multimodal RAG system. "
            "You answer questions based on indexed media: images, videos, and documents. "
            "IMPORTANT: When the user asks to see images or files, tell them the images are displayed "
            "in the Sources panel below your response — do NOT say you cannot display images. "
            "Use the provided context to answer accurately. "
            "If an image is relevant, describe what it shows AND mention it will appear in Sources below. "
            "If context is insufficient, say so honestly. "
            "Be concise and cite the source filename when relevant."
        )

        user_content = f"Context from indexed files:\n{context}\n\nQuestion: {message}"

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            stream=True,
            temperature=0.3,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def format_context(self, results: list[dict]) -> str:
        if not results:
            return "No relevant content found in the indexed files."

        parts = []
        for i, r in enumerate(results, start=1):
            meta = r.get("metadata", {})
            score = r.get("score", 0)
            r_type = meta.get("type", "unknown")

            if r_type == "document_chunk":
                parts.append(
                    f"[{i}] Document '{meta.get('filename', '?')}' page {meta.get('page', '?')} "
                    f"(score={score:.2f}):\n{meta.get('text', '')}"
                )
            elif r_type in ("image", "video_frame"):
                parts.append(
                    f"[{i}] {r_type.replace('_', ' ').title()} '{meta.get('filename', '?')}' "
                    f"(score={score:.2f}):\n{meta.get('description', 'No description available.')}"
                )
            else:
                parts.append(f"[{i}] {r_type} '{meta.get('filename', '?')}' (score={score:.2f})")

        full_context = "\n\n".join(parts)
        return full_context[:MAX_CONTEXT_CHARS]

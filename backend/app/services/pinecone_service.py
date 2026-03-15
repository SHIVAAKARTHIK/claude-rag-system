from pinecone import Pinecone, ServerlessSpec
from tenacity import retry, stop_after_attempt, wait_fixed
from app.core.config import settings


class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self._ensure_index()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index(self):
        existing = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing:
            self.pc.create_index(
                name=self.index_name,
                dimension=settings.PINECONE_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def upsert(self, vectors: list[dict]):
        """vectors: list of {id, values, metadata}"""
        self.index.upsert(vectors=vectors)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter: dict | None = None,
    ) -> list[dict]:
        kwargs = {"vector": embedding, "top_k": top_k, "include_metadata": True}
        if filter:
            kwargs["filter"] = filter
        result = self.index.query(**kwargs)
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata or {},
            }
            for match in result.matches
        ]

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def delete(self, ids: list[str]):
        self.index.delete(ids=ids)

    def get_stats(self) -> dict:
        stats = self.index.describe_index_stats()
        return {
            "total_vector_count": stats.total_vector_count,
            "dimension": stats.dimension,
            "namespaces": dict(stats.namespaces) if stats.namespaces else {},
        }

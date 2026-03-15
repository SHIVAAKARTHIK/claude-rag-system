"""
Initialize the Pinecone index for the Multimodal RAG system.
Run from the backend/ directory: python ../tools/pinecone_init.py
"""
import sys
import os

# Allow running from tools/ or backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from pinecone import Pinecone, ServerlessSpec

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "multimodal-rag")
DIMENSION = 1536  # text-embedding-3-large
REGION = "us-east-1"
CLOUD = "aws"


def init_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = [idx.name for idx in pc.list_indexes()]

    if INDEX_NAME in existing:
        print(f"Index '{INDEX_NAME}' already exists.")
        stats = pc.Index(INDEX_NAME).describe_index_stats()
        print(f"  Vectors: {stats.total_vector_count}")
        print(f"  Dimension: {stats.dimension}")
        return

    print(f"Creating index '{INDEX_NAME}' ({DIMENSION}d, cosine, serverless {CLOUD}/{REGION})...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=CLOUD, region=REGION),
    )
    print(f"Index '{INDEX_NAME}' created successfully.")


if __name__ == "__main__":
    init_index()

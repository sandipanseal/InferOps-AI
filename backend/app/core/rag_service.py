import uuid
from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()

VECTOR_SIZE = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_name)


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    client = get_qdrant_client()

    collections = client.get_collections().collections
    existing_collection_names = {collection.name for collection in collections}

    if settings.rag_collection_name not in existing_collection_names:
        client.create_collection(
            collection_name=settings.rag_collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )


def chunk_text(text: str, chunk_size: int = 180, overlap: int = 40) -> list[str]:
    words = text.split()

    if not words:
        return []

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)

    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])

        if chunk.strip():
            chunks.append(chunk)

    return chunks


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def upload_document_to_qdrant(
    document_name: str,
    text: str,
    source_type: str = "file",
    filename: str | None = None,
) -> dict[str, Any]:
    ensure_collection()

    client = get_qdrant_client()
    chunks = chunk_text(text)

    document_id = str(uuid.uuid4())
    points: list[PointStruct] = []

    for chunk_index, chunk in enumerate(chunks):
        point_id = str(uuid.uuid4())

        points.append(
            PointStruct(
                id=point_id,
                vector=embed_text(chunk),
                payload={
                    "document_id": document_id,
                    "document_name": document_name,
                    "filename": filename or document_name,
                    "source_type": source_type,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk,
                    "characters": len(chunk),
                },
            )
        )

    if points:
        client.upsert(
            collection_name=settings.rag_collection_name,
            points=points,
        )

    return {
        "document_id": document_id,
        "document_name": document_name,
        "filename": filename or document_name,
        "source_type": source_type,
        "chunks_created": len(points),
        "characters_indexed": len(text),
    }


def query_knowledge(
    query: str,
    top_k: int = 5,
    document_name: str | None = None,
) -> dict[str, Any]:
    ensure_collection()

    client = get_qdrant_client()
    query_vector = embed_text(query)

    query_filter = None

    if document_name:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name),
                )
            ]
        )

    response = client.query_points(
        collection_name=settings.rag_collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    matches: list[dict[str, Any]] = []

    for point in response.points:
        payload = point.payload or {}

        matches.append(
            {
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name", "unknown"),
                "filename": payload.get("filename"),
                "source_type": payload.get("source_type"),
                "chunk_index": payload.get("chunk_index"),
                "chunk_text": payload.get("chunk_text", ""),
                "score": round(float(point.score), 4),
            }
        )

    return {
        "query": query,
        "document_name": document_name,
        "matches": matches,
    }


def build_rag_context(
    query: str,
    top_k: int = 5,
    min_score: float = 0.20,
    document_name: str | None = None,
) -> str:
    result = query_knowledge(
        query=query,
        top_k=top_k,
        document_name=document_name,
    )

    matches = [
        match
        for match in result["matches"]
        if float(match.get("score", 0)) >= min_score
    ]

    if not matches:
        return ""

    context_parts: list[str] = []

    for index, match in enumerate(matches, start=1):
        context_parts.append(
            f"[Source {index} | document={match['document_name']} | "
            f"filename={match.get('filename')} | chunk={match['chunk_index']} | "
            f"score={match['score']}]\n"
            f"{match['chunk_text']}"
        )

    return "\n\n".join(context_parts)


def list_documents() -> list[dict[str, Any]]:
    ensure_collection()

    client = get_qdrant_client()

    points, _ = client.scroll(
        collection_name=settings.rag_collection_name,
        limit=10_000,
        with_payload=True,
        with_vectors=False,
    )

    docs: dict[str, dict[str, Any]] = {}

    for point in points:
        payload = point.payload or {}
        name = payload.get("document_name", "unknown")

        if name not in docs:
            docs[name] = {
                "document_id": payload.get("document_id"),
                "document_name": name,
                "filename": payload.get("filename", name),
                "source_type": payload.get("source_type", "unknown"),
                "chunks": 0,
            }

        docs[name]["chunks"] += 1

    return list(docs.values())


def delete_document(document_name: str) -> dict[str, Any]:
    ensure_collection()

    client = get_qdrant_client()

    client.delete(
        collection_name=settings.rag_collection_name,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_name",
                        match=MatchValue(value=document_name),
                    )
                ]
            )
        ),
    )

    return {
        "deleted": True,
        "document_name": document_name,
    }


def clear_knowledge_base() -> dict[str, Any]:
    client = get_qdrant_client()

    collections = client.get_collections().collections
    existing_collection_names = {collection.name for collection in collections}

    if settings.rag_collection_name in existing_collection_names:
        client.delete_collection(collection_name=settings.rag_collection_name)

    ensure_collection()

    return {
        "cleared": True,
        "collection": settings.rag_collection_name,
    }

def retrieve_rag_context_with_metadata(
    query: str,
    top_k: int = 5,
    min_score: float = 0.20,
    document_name: str | None = None,
) -> dict[str, Any]:
    result = query_knowledge(
        query=query,
        top_k=top_k,
        document_name=document_name,
    )

    matches = [
        match
        for match in result["matches"]
        if float(match.get("score", 0)) >= min_score
    ]

    if not matches:
        return {
            "context": "",
            "rag_used": False,
            "rag_document": None,
            "rag_filename": None,
            "rag_chunks": 0,
            "rag_top_score": None,
        }

    context_parts = []

    for index, match in enumerate(matches, start=1):
        context_parts.append(
            f"[Source {index} | document={match['document_name']} | "
            f"filename={match.get('filename')} | chunk={match['chunk_index']} | "
            f"score={match['score']}]\n"
            f"{match['chunk_text']}"
        )

    top_match = matches[0]

    return {
        "context": "\n\n".join(context_parts),
        "rag_used": True,
        "rag_document": top_match.get("document_name"),
        "rag_filename": top_match.get("filename"),
        "rag_chunks": len(matches),
        "rag_top_score": float(top_match.get("score", 0)),
    }
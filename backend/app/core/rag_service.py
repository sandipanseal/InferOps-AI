"""RAG service.

pgvector (Postgres) implementation. Drop-in replacement for the previous
Qdrant version — all public functions keep their original names and
signatures so that routes_rag.py, routes_chat.py, rag_agent.py, and
ragas_eval.py work unchanged.

Connection is taken from settings.database_url. Supports both
postgresql+asyncpg://… (async) and plain postgresql://… URLs by rewriting
to a sync psycopg2 DSN locally — pgvector indexing is done synchronously
because it runs inside a single request lifetime and is fast.

Schema:
    rag_chunks(
        id            UUID PRIMARY KEY,
        document_id   UUID,
        document_name TEXT,
        filename      TEXT,
        source_type   TEXT,
        chunk_index   INT,
        chunk_text    TEXT,
        characters    INT,
        embedding     vector(384)
    )

Tables and the pgvector extension are created lazily on first use so the
service works against a fresh Supabase project with no migration step.
"""
from __future__ import annotations

import os
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import psycopg2
import psycopg2.extras

from app.config import get_settings

# sentence_transformers transitively imports torch (~5-7s on Lambda cold start),
# which alone blows past Lambda's 10s init-phase ceiling. We defer the import
# inside get_embedding_model() so the cost is paid on the first RAG request,
# not at every cold start. The TYPE_CHECKING branch keeps static type checkers
# happy without triggering the runtime import.
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

settings = get_settings()

VECTOR_SIZE = 384
TABLE_NAME = "rag_chunks"

_tables_ready = False


# ── Helpers ───────────────────────────────────────────────────────────────────


def _sync_dsn() -> str:
    """Return a psycopg2-compatible DSN derived from settings.database_url."""
    url = settings.database_url
    # SQLAlchemy-style async URL → psycopg2 sync URL
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return url


_LAMBDA_LOCAL_MODEL_PATH = "/var/task/embedding_model"


@lru_cache(maxsize=1)
def get_embedding_model() -> "SentenceTransformer":
    # Deferred import — see top-of-file comment. lru_cache means torch +
    # the model load happen exactly once per warm container, on the first
    # RAG-touching request.
    from sentence_transformers import SentenceTransformer

    # In Lambda the model is baked as a self-contained directory by the
    # Dockerfile (`SentenceTransformer.save('/var/task/embedding_model')`).
    # Passing that directory to SentenceTransformer triggers a pure local-
    # file load with no HF Hub network/cache code path — sidestepping the
    # version-skew across sentence-transformers / transformers /
    # huggingface_hub cache-layout conventions that bit us before.
    #
    # Outside Lambda (local dev, CI) the directory doesn't exist and we
    # fall back to the standard repo-id load against the writable user
    # cache.
    if os.path.isdir(_LAMBDA_LOCAL_MODEL_PATH):
        return SentenceTransformer(_LAMBDA_LOCAL_MODEL_PATH)
    return SentenceTransformer(settings.embedding_model_name)


def _get_conn():
    """Open a fresh psycopg2 connection.

    A new connection per call keeps things simple in Lambda where containers
    can be paused for long stretches and connections silently die. Supabase
    pooler handles the upstream side.
    """
    conn = psycopg2.connect(_sync_dsn())
    conn.autocommit = True
    return conn


def _ensure_tables() -> None:
    """Create pgvector extension, table, and ivfflat index on first use."""
    global _tables_ready
    if _tables_ready:
        return

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id            UUID PRIMARY KEY,
                    document_id   UUID NOT NULL,
                    document_name TEXT NOT NULL,
                    filename      TEXT,
                    source_type   TEXT,
                    chunk_index   INT,
                    chunk_text    TEXT NOT NULL,
                    characters    INT,
                    embedding     vector({VECTOR_SIZE})
                );
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {TABLE_NAME}_document_name_idx
                ON {TABLE_NAME} (document_name);
                """
            )
            # IVFFlat clusters vectors into `lists` buckets and at query time
            # searches only `ivfflat.probes` (default 1) of them. With our
            # dataset (often <100 chunks during demos / tests) the single
            # probed bucket usually doesn't contain the matching row and
            # the query returns zero results, even though the row is there
            # — visible immediately when you add a WHERE filter that lets
            # Postgres pick a sequential-scan plan instead.
            #
            # HNSW has no probe parameter and works correctly for any
            # dataset size, so we drop the legacy IVFFlat index (idempotent
            # if it never existed) and replace it with HNSW. pgvector
            # >= 0.5 ships HNSW; Supabase has shipped pgvector >= 0.5 since
            # 2024 so this is safe.
            cur.execute(
                f"DROP INDEX IF EXISTS {TABLE_NAME}_embedding_idx;"
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {TABLE_NAME}_embedding_hnsw_idx
                ON {TABLE_NAME} USING hnsw (embedding vector_cosine_ops);
                """
            )
        _tables_ready = True
    finally:
        conn.close()


def _vector_literal(vec: list[float]) -> str:
    """pgvector accepts vectors as '[0.1,0.2,...]' string literals."""
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


# ── Existing public helpers (kept) ───────────────────────────────────────────

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


# ── Public API (signatures preserved exactly) ────────────────────────────────


def ensure_collection() -> None:
    """Compatibility alias — old code called this to lazily set up the store."""
    _ensure_tables()


def upload_document_to_qdrant(
    document_name: str,
    text: str,
    source_type: str = "file",
    filename: str | None = None,
) -> dict[str, Any]:
    """Name preserved for caller compatibility — now writes to pgvector."""
    _ensure_tables()

    chunks = chunk_text(text)
    document_id = str(uuid.uuid4())

    if not chunks:
        return {
            "document_id": document_id,
            "document_name": document_name,
            "filename": filename or document_name,
            "source_type": source_type,
            "chunks_created": 0,
            "characters_indexed": len(text),
        }

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            for chunk_index, chunk in enumerate(chunks):
                cur.execute(
                    f"""
                    INSERT INTO {TABLE_NAME}
                        (id, document_id, document_name, filename, source_type,
                         chunk_index, chunk_text, characters, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                    """,
                    (
                        str(uuid.uuid4()),
                        document_id,
                        document_name,
                        filename or document_name,
                        source_type,
                        chunk_index,
                        chunk,
                        len(chunk),
                        _vector_literal(embed_text(chunk)),
                    ),
                )
    finally:
        conn.close()

    return {
        "document_id": document_id,
        "document_name": document_name,
        "filename": filename or document_name,
        "source_type": source_type,
        "chunks_created": len(chunks),
        "characters_indexed": len(text),
    }


def query_knowledge(
    query: str,
    top_k: int = 5,
    document_name: str | None = None,
) -> dict[str, Any]:
    _ensure_tables()

    query_vec = _vector_literal(embed_text(query))
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if document_name:
                cur.execute(
                    f"""
                    SELECT
                        document_id,
                        document_name,
                        filename,
                        source_type,
                        chunk_index,
                        chunk_text,
                        1 - (embedding <=> %s::vector) AS score
                    FROM {TABLE_NAME}
                    WHERE document_name = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_vec, document_name, query_vec, top_k),
                )
            else:
                cur.execute(
                    f"""
                    SELECT
                        document_id,
                        document_name,
                        filename,
                        source_type,
                        chunk_index,
                        chunk_text,
                        1 - (embedding <=> %s::vector) AS score
                    FROM {TABLE_NAME}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_vec, query_vec, top_k),
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    matches: list[dict[str, Any]] = []
    for row in rows:
        matches.append(
            {
                "document_id": str(row["document_id"]) if row["document_id"] else None,
                "document_name": row.get("document_name", "unknown"),
                "filename": row.get("filename"),
                "source_type": row.get("source_type"),
                "chunk_index": row.get("chunk_index"),
                "chunk_text": row.get("chunk_text", ""),
                "score": round(float(row["score"]), 4) if row.get("score") is not None else 0.0,
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
    _ensure_tables()

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT
                    document_id,
                    document_name,
                    MAX(filename)    AS filename,
                    MAX(source_type) AS source_type,
                    COUNT(*)         AS chunks
                FROM {TABLE_NAME}
                GROUP BY document_id, document_name
                ORDER BY document_name
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "document_id": str(row["document_id"]) if row["document_id"] else None,
            "document_name": row.get("document_name", "unknown"),
            "filename": row.get("filename") or row.get("document_name", "unknown"),
            "source_type": row.get("source_type") or "unknown",
            "chunks": int(row.get("chunks", 0)),
        }
        for row in rows
    ]


def delete_document(document_name: str) -> dict[str, Any]:
    _ensure_tables()

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE_NAME} WHERE document_name = %s",
                (document_name,),
            )
    finally:
        conn.close()

    return {
        "deleted": True,
        "document_name": document_name,
    }


def clear_knowledge_base() -> dict[str, Any]:
    _ensure_tables()

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {TABLE_NAME}")
    finally:
        conn.close()

    return {
        "cleared": True,
        "collection": TABLE_NAME,
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

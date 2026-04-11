"""
Vector Store Service – ChromaDB wrapper.
Uses PersistentClient (embedded) so no separate ChromaDB server is needed.
Works on Render free tier and locally.
"""
import os
import chromadb
import structlog
from app.core.config import settings

log = structlog.get_logger()

# Persistent storage path — on Render this lives in /app/chroma_data
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "/app/chroma_data")


def _get_client() -> chromadb.PersistentClient:
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def index_document(document_id: int, chunks: list[dict], embeddings: list[list[float]]) -> int:
    """Index document chunks into ChromaDB. Returns chunk count."""
    client = _get_client()
    collection_name = f"{settings.CHROMA_COLLECTION_NAME}_{document_id}"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"doc{document_id}_chunk{c['chunk_index']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{"chunk_index": c["chunk_index"], "token_count": c.get("token_count", 0)} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    log.info("Document indexed", document_id=document_id, chunk_count=len(chunks))
    return len(chunks)


def search_document(document_id: int, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Search a single document's ChromaDB collection."""
    client = _get_client()
    collection_name = f"{settings.CHROMA_COLLECTION_NAME}_{document_id}"

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return []

    count = collection.count()
    if count == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        distance = results["distances"][0][i]
        score = max(0.0, 1.0 - distance)
        chunks.append({
            "text": doc,
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "relevance_score": round(score, 4),
        })
    return chunks


def search_all_user_documents(
    document_ids: list[int],
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict]:
    """Search across all of a user's documents, return top-k by score."""
    all_results = []
    for doc_id in document_ids:
        chunks = search_document(doc_id, query_embedding, top_k=top_k)
        for chunk in chunks:
            chunk["document_id"] = doc_id
        all_results.extend(chunks)
    all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return all_results[:top_k]


def search_knowledge_base(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Search the pre-loaded Kenyan law knowledge base collection.
    Called when user document retrieval scores are below the confidence threshold.
    """
    client = _get_client()
    try:
        collection = client.get_collection(settings.KB_COLLECTION_NAME)
    except Exception:
        log.warning("Knowledge base collection not found")
        return []

    count = collection.count()
    if count == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        distance = results["distances"][0][i]
        score = max(0.0, 1.0 - distance)
        meta = results["metadatas"][0][i]
        chunks.append({
            "text": doc,
            "chunk_index": meta.get("chunk_index", i),
            "relevance_score": round(score, 4),
            "source": meta.get("source", "Kenyan Law Knowledge Base"),
            "document_id": 0,
        })
    return chunks


def delete_document_collection(document_id: int):
    """Delete all embeddings for a document from ChromaDB."""
    client = _get_client()
    try:
        client.delete_collection(f"{settings.CHROMA_COLLECTION_NAME}_{document_id}")
        log.info("Collection deleted", document_id=document_id)
    except Exception as e:
        log.warning("Collection not found on delete", document_id=document_id, error=str(e))


async def delete_document_chunks(doc_id: int) -> None:
    """Remove all ChromaDB embeddings for a given document_id."""
    try:
        client = _get_client()
        collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        results = collection.get(where={"document_id": doc_id})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            log.info("ChromaDB chunks deleted", doc_id=doc_id, count=len(ids_to_delete))
    except Exception as e:
        log.warning("delete_document_chunks failed", doc_id=doc_id, error=str(e))
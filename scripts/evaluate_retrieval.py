"""
Retrieval Evaluation Script
Measures Precision@K and Recall@K for the RAG retrieval pipeline.

Usage:
  python scripts/evaluate_retrieval.py

Sample queries and ground-truth relevant document IDs must be defined below.
"""
import sys
sys.path.insert(0, "../backend")

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import search_document


# ── Define test cases ─────────────────────────────────────────
# Each case: (query, document_id, list_of_relevant_chunk_indices)
TEST_CASES = [
    {
        "query": "What are the termination clauses?",
        "document_id": 1,
        "relevant_chunks": [0, 2, 5],  # Ground truth chunk indices
    },
    {
        "query": "Ni nini masharti ya kufuta mkataba?",  # Swahili
        "document_id": 1,
        "relevant_chunks": [0, 2, 5],
    },
    {
        "query": "What are the liability limitations?",
        "document_id": 1,
        "relevant_chunks": [3, 7],
    },
]


def precision_at_k(retrieved: list[int], relevant: set[int], k: int) -> float:
    """Precision@K = |retrieved[:k] ∩ relevant| / k"""
    retrieved_k = set(retrieved[:k])
    return len(retrieved_k & relevant) / k if k > 0 else 0.0


def recall_at_k(retrieved: list[int], relevant: set[int], k: int) -> float:
    """Recall@K = |retrieved[:k] ∩ relevant| / |relevant|"""
    retrieved_k = set(retrieved[:k])
    return len(retrieved_k & relevant) / len(relevant) if relevant else 0.0


def evaluate(k: int = 5):
    embedder = EmbeddingService.get_instance()
    precisions = []
    recalls = []

    for case in TEST_CASES:
        query_emb = embedder.embed_single(case["query"])
        results = search_document(case["document_id"], query_emb, top_k=k)
        retrieved_indices = [r["chunk_index"] for r in results]
        relevant_set = set(case["relevant_chunks"])

        p = precision_at_k(retrieved_indices, relevant_set, k)
        r = recall_at_k(retrieved_indices, relevant_set, k)
        precisions.append(p)
        recalls.append(r)

        print(f"Query: {case['query'][:50]}...")
        print(f"  Precision@{k}: {p:.3f} | Recall@{k}: {r:.3f}")
        print(f"  Retrieved: {retrieved_indices} | Relevant: {list(relevant_set)}")

    print(f"\n── Summary ──────────────────────────────")
    print(f"  Mean Precision@{k}: {sum(precisions)/len(precisions):.3f}")
    print(f"  Mean Recall@{k}:    {sum(recalls)/len(recalls):.3f}")


if __name__ == "__main__":
    evaluate(k=5)

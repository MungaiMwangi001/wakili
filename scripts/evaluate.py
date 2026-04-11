#!/usr/bin/env python3
"""
scripts/evaluate.py
────────────────────
Offline evaluation of the Wakili RAG pipeline.

Metrics computed:
  • Precision@K  – fraction of retrieved chunks that are relevant
  • Recall@K     – fraction of relevant chunks retrieved in top K
  • ROUGE-1/2/L  – n-gram overlap between generated answer and reference

Usage:
  python scripts/evaluate.py --testset scripts/test_queries.jsonl --top-k 5

Test set format (JSONL):
  {"query": "What are the termination clauses?", "doc_id": "...", "relevant_chunk_ids": ["id1","id2"], "reference_answer": "..."}
"""

import argparse
import json
import time
from pathlib import Path
from typing import List, Dict

import numpy as np
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer
import chromadb

# ── Config ────────────────────────────────────────────────────────
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
COLLECTION  = "wakili_docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_test_set(path: str) -> List[Dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """P@K = |retrieved[:K] ∩ relevant| / K"""
    top_k = set(retrieved[:k])
    return len(top_k & set(relevant)) / k if k else 0.0


def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """R@K = |retrieved[:K] ∩ relevant| / |relevant|"""
    if not relevant:
        return 0.0
    top_k = set(retrieved[:k])
    return len(top_k & set(relevant)) / len(relevant)


def compute_rouge(hypothesis: str, reference: str) -> Dict[str, float]:
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return {
        "rouge1": scores["rouge1"].fmeasure,
        "rouge2": scores["rouge2"].fmeasure,
        "rougeL": scores["rougeL"].fmeasure,
    }


def run_evaluation(testset_path: str, top_k: int = 5):
    print(f"\n{'='*60}")
    print(f" Wakili RAG Evaluation  |  top-K={top_k}")
    print(f"{'='*60}\n")

    # Load embedding model and ChromaDB
    print("Loading embedding model…")
    embedder = SentenceTransformer(EMBED_MODEL)
    chroma   = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    coll     = chroma.get_collection(COLLECTION)

    test_cases = load_test_set(testset_path)
    print(f"Loaded {len(test_cases)} test queries.\n")

    precision_scores, recall_scores, rouge_scores = [], [], []
    latencies = []

    for i, tc in enumerate(test_cases):
        query     = tc["query"]
        relevant  = tc.get("relevant_chunk_ids", [])
        reference = tc.get("reference_answer", "")
        doc_id    = tc.get("doc_id")

        # Embed query
        t0 = time.perf_counter()
        embedding = embedder.encode([query])[0].tolist()

        # Retrieve
        where = {"doc_id": doc_id} if doc_id else None
        results = coll.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "ids"],
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        retrieved_ids = results["ids"][0] if results["ids"] else []
        retrieved_docs = results["documents"][0] if results["documents"] else []

        # Metrics
        p = precision_at_k(retrieved_ids, relevant, top_k)
        r = recall_at_k(retrieved_ids, relevant, top_k)
        precision_scores.append(p)
        recall_scores.append(r)

        # ROUGE (if reference answer provided)
        if reference and retrieved_docs:
            generated = " ".join(retrieved_docs[:2])  # simulate short answer
            rouge = compute_rouge(generated, reference)
            rouge_scores.append(rouge)

        print(f"[{i+1:02d}] {query[:55]:<55} P@{top_k}={p:.2f}  R@{top_k}={r:.2f}  {latency_ms:.0f}ms")

    # Aggregate
    print(f"\n{'─'*60}")
    print(f"  Mean Precision@{top_k}:   {np.mean(precision_scores):.4f}")
    print(f"  Mean Recall@{top_k}:      {np.mean(recall_scores):.4f}")
    if rouge_scores:
        print(f"  Mean ROUGE-1:         {np.mean([s['rouge1'] for s in rouge_scores]):.4f}")
        print(f"  Mean ROUGE-2:         {np.mean([s['rouge2'] for s in rouge_scores]):.4f}")
        print(f"  Mean ROUGE-L:         {np.mean([s['rougeL'] for s in rouge_scores]):.4f}")
    print(f"  Mean Latency:         {np.mean(latencies):.1f} ms")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wakili RAG Evaluation")
    parser.add_argument("--testset", default="scripts/test_queries.jsonl", help="Path to JSONL test set")
    parser.add_argument("--top-k",  type=int, default=5, help="Top-K chunks to retrieve")
    args = parser.parse_args()
    run_evaluation(args.testset, args.top_k)

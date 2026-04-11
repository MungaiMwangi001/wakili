"""
ROUGE Evaluation Script
Measures ROUGE-1, ROUGE-2, ROUGE-L between generated and reference answers.

Usage:
  python scripts/evaluate_rouge.py

Reference answers must be manually curated for your test documents.
"""
from rouge_score import rouge_scorer

# ── Ground truth pairs: (generated_answer, reference_answer) ──
# Replace with real outputs from your RAG pipeline
EVAL_PAIRS = [
    {
        "question": "What are the termination clauses?",
        "generated": "The contract may be terminated with 30 days written notice by either party.",
        "reference": "Either party may terminate the agreement with 30 days' written notice.",
    },
    {
        "question": "Ni nini masharti ya kufuta mkataba?",
        "generated": "Mkataba unaweza kufutwa kwa taarifa ya siku 30 kwa maandishi.",
        "reference": "Mkataba unaweza kusimamishwa kwa taarifa ya maandishi ya siku 30.",
    },
]


def evaluate_rouge():
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    all_scores = {"rouge1": [], "rouge2": [], "rougeL": []}

    for pair in EVAL_PAIRS:
        scores = scorer.score(pair["reference"], pair["generated"])
        print(f"Q: {pair['question'][:60]}")
        for metric, score in scores.items():
            print(f"  {metric}: P={score.precision:.3f} R={score.recall:.3f} F={score.fmeasure:.3f}")
            all_scores[metric].append(score.fmeasure)

    print("\n── Mean F1 Scores ───────────────────────")
    for metric, scores in all_scores.items():
        print(f"  {metric}: {sum(scores)/len(scores):.3f}")


if __name__ == "__main__":
    evaluate_rouge()

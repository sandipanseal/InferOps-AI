"""
RAGAS evaluation: faithfulness and context precision.

RAGAS scores RAG pipelines on grounded metrics:

  - faithfulness         : fraction of claims in the answer that are supported
                           by the retrieved context (1.0 = perfectly grounded,
                           0.0 = hallucinated).
  - context_precision    : average precision of the retrieved chunks ordered
                           by relevance to the ground-truth answer.

This module accepts a list of evaluation samples, each with:

    {
      "question":     "...",
      "answer":       "...",          # what the gateway answered
      "contexts":     ["chunk1", ...] # what RAG retrieved
      "ground_truth": "..."           # what the correct answer is
    }

If `contexts` is omitted, this module will call the InferOps RAG retriever to
fetch them so you can evaluate the production retrieval path directly.

RAGAS itself uses an LLM judge (OpenAI by default) to score faithfulness and
context precision. We do not re-implement those metrics; we delegate to the
official `ragas` package.
"""

from __future__ import annotations

import os
from typing import Any

from app.core.rag_service import query_knowledge


def _ensure_contexts(samples: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    enriched = []
    for sample in samples:
        contexts = sample.get("contexts")
        if not contexts:
            result = query_knowledge(query=sample["question"], top_k=top_k)
            contexts = [m["chunk_text"] for m in result.get("matches", [])]
        enriched.append({**sample, "contexts": contexts})
    return enriched


def run_ragas_eval(
    samples: list[dict[str, Any]],
    top_k: int = 4,
) -> dict[str, Any]:
    """Evaluate samples with RAGAS faithfulness + context_precision."""

    if not samples:
        return {"ok": False, "error": "no samples provided", "scores": {}}

    if not os.getenv("OPENAI_API_KEY"):
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not configured. RAGAS metrics use an LLM judge.",
            "scores": {},
        }

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import context_precision, faithfulness
    except ImportError as exc:
        return {
            "ok": False,
            "error": f"RAGAS dependencies missing: {exc}. Install ragas and datasets.",
            "scores": {},
        }

    enriched = _ensure_contexts(samples, top_k=top_k)

    dataset = Dataset.from_list(
        [
            {
                "question": s["question"],
                "answer": s.get("answer", ""),
                "contexts": s["contexts"],
                "ground_truth": s.get("ground_truth", ""),
            }
            for s in enriched
        ]
    )

    result = evaluate(dataset, metrics=[faithfulness, context_precision])

    # ragas Result -> dict of metric -> mean float, plus per-row scores
    aggregate = {k: float(v) for k, v in result.to_pandas().mean(numeric_only=True).to_dict().items()}

    per_row = result.to_pandas().to_dict(orient="records")

    return {
        "ok": True,
        "scores": aggregate,
        "samples": per_row,
        "total_samples": len(enriched),
    }

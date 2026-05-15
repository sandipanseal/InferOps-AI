def estimate_complexity(prompt: str, task_type: str) -> float:
    text = prompt.lower()
    length_score = min(len(prompt) / 4000, 1.0)

    hard_keywords = [
        "reason", "analyze", "strategy", "architecture", "debug", "legal",
        "contract", "risk", "multi-step", "evaluate", "compare", "derive"
    ]
    simple_keywords = [
        "classify", "summarize", "extract", "rewrite", "translate", "short"
    ]

    score = 0.25 + 0.45 * length_score

    if any(k in text for k in hard_keywords):
        score += 0.35
    if any(k in text for k in simple_keywords):
        score -= 0.15
    if task_type in {"classification", "simple_summary"}:
        score -= 0.2
    if task_type in {"reasoning", "analysis", "coding"}:
        score += 0.25

    return max(0.0, min(score, 1.0))

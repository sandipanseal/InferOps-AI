"""
LLM-as-judge eval layer.

Runs the deterministic routing eval suite, then asks GPT-4 to score the
quality of each routing decision on a 1-5 scale with a written rationale.

This catches "passed the assertion but for the wrong reason" cases that pure
exact-match evals cannot. For example, a request that *should* have gone to
the premium model but went there because complexity overshot due to length
alone will still get a low judge score.

Scoring rubric given to the judge:
  5 - optimal routing decision, well-justified
  4 - reasonable decision, minor concerns
  3 - acceptable, but a better route exists
  2 - clearly suboptimal
  1 - wrong route (e.g. PII leaked to cloud)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

from app.evals.eval_runner import run_eval_suite


JUDGE_SYSTEM_PROMPT = """You are an expert LLM-gateway routing reviewer.

You will receive a routing case with:
  - input prompt
  - user priority (cost_optimized | quality_optimized | latency_optimized)
  - privacy mode (normal | sensitive | local_only)
  - contains_pii (true|false): whether the gateway's PII detector fired
  - prompt_injection_risk (low|medium|high)
  - safety_blocked (true|false)
  - the model the gateway actually selected
  - the provider
  - the complexity score the gateway computed (0..1)
  - the routing reason

Gateway policy you MUST treat as ground truth:
  - If contains_pii is true, the request MUST be routed to a local model regardless of priority or privacy mode. This is a privacy/compliance requirement, not a cost decision.
  - If privacy is "sensitive" or "local_only", routing MUST stay local.
  - If safety_blocked is true, the gateway MUST refuse to call any model.
  - quality_optimized + high complexity should use the premium provider.
  - cost_optimized + low complexity should use the cheapest provider.

Score the routing decision from 1 to 5 using this rubric:
  5 - optimal routing decision, well-justified, fully consistent with the policy above
  4 - reasonable decision, minor concerns
  3 - acceptable, but a better route exists
  2 - clearly suboptimal
  1 - wrong route (e.g. PII leaked to a cloud provider, or premium model used for trivial classification)

Reply with STRICT JSON only, no prose, no markdown fences:
{"score": <int 1-5>, "rationale": "<one sentence>"}
"""


def _judge_one(case: dict[str, Any], judge_model: str, api_key: str) -> dict[str, Any]:
    user_block = (
        f"input: {case.get('input')}\n"
        f"priority: {case.get('priority')}\n"
        f"privacy: {case.get('privacy')}\n"
        f"contains_pii: {case.get('contains_pii')}\n"
        f"prompt_injection_risk: {case.get('prompt_injection_risk')}\n"
        f"safety_blocked: {case.get('safety_blocked')}\n"
        f"selected_model: {case.get('actual_model')}\n"
        f"selected_provider: {case.get('actual_provider')}\n"
        f"complexity_score: {case.get('complexity_score')}\n"
        f"routing_reason: {case.get('routing_reason')}\n"
    )

    with httpx.Client(timeout=30) as client:
        res = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": judge_model,
                "messages": [
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_block},
                ],
                "temperature": 0,
                "max_tokens": 200,
            },
        )
        res.raise_for_status()
        data = res.json()

    raw = data["choices"][0]["message"]["content"].strip()
    # tolerate accidental code fences
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(raw)
        score = int(parsed.get("score", 0))
        rationale = str(parsed.get("rationale", ""))[:500]
    except Exception:
        score = 0
        rationale = f"could not parse judge output: {raw[:200]}"

    return {"score": score, "rationale": rationale, "judge_model": judge_model}


def run_judge_eval(judge_model: str = "gpt-4o") -> dict[str, Any]:
    """Run the routing eval suite, then score every case with an LLM judge.

    Returns aggregate average score plus per-case scores. Fails soft if no
    OPENAI_API_KEY is configured."""

    base = run_eval_suite()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not configured.",
            "eval": base,
        }

    judged = []
    for case in base["cases"]:
        try:
            verdict = _judge_one(case, judge_model, api_key)
        except Exception as exc:  # noqa: BLE001
            verdict = {"score": 0, "rationale": f"judge call failed: {exc}", "judge_model": judge_model}

        judged.append({**case, "judge": verdict})

    valid_scores = [c["judge"]["score"] for c in judged if c["judge"]["score"] > 0]
    avg = round(sum(valid_scores) / len(valid_scores), 3) if valid_scores else 0.0

    return {
        "ok": True,
        "judge_model": judge_model,
        "average_judge_score": avg,
        "max_score": 5,
        "scored_cases": len(valid_scores),
        "total_cases": len(judged),
        "routing_accuracy": base.get("routing_accuracy"),
        "cases": judged,
    }

"""
LangChain agentic workflow.

The agent is given a question and a set of tools:

  - `rag_search`         : retrieve top-k chunks from the Qdrant knowledge base
  - `routing_decision`   : ask the InferOps router which model would serve a prompt
  - `complexity_score`   : score the complexity of a prompt with the same heuristic
                          used by the production router

The agent reasons step-by-step (ReAct), calls one or more tools, and produces a
final natural-language answer with citations.

The LLM backing the agent is OpenAI by design (gpt-4o-mini by default) because
LangChain's tool-calling agent needs a function-calling capable model. If
`OPENAI_API_KEY` is not set, the endpoint returns a clear error.
"""

from __future__ import annotations

import os
from typing import Any

from app.core.complexity import estimate_complexity
from app.core.rag_service import query_knowledge
from app.core.router import route_request
from app.schemas import ChatRequest, SafetyResult


def _build_tools():
    from langchain_core.tools import tool

    @tool
    def rag_search(query: str, top_k: int = 4) -> str:
        """Search the InferOps knowledge base (Qdrant) for chunks relevant to `query`.
        Returns the top-k chunks with their document names and similarity scores."""
        result = query_knowledge(query=query, top_k=top_k)
        matches = result.get("matches", [])

        if not matches:
            return "No relevant context found in the knowledge base."

        lines: list[str] = []
        for index, match in enumerate(matches, start=1):
            lines.append(
                f"[{index}] document={match['document_name']} "
                f"chunk={match['chunk_index']} score={match['score']}\n"
                f"{match['chunk_text']}"
            )
        return "\n\n".join(lines)

    @tool
    def routing_decision(prompt: str, priority: str = "cost_optimized") -> str:
        """Ask the InferOps router which model would handle `prompt` under the given
        priority (cost_optimized | quality_optimized | latency_optimized).
        Returns the selected model, provider, complexity score, and routing reason."""
        req = ChatRequest(
            user_id="agent",
            input=prompt,
            task_type="auto",
            priority=priority if priority in {"cost_optimized", "quality_optimized", "latency_optimized"} else "cost_optimized",
            privacy="normal",
        )
        safety = SafetyResult()
        decision = route_request(
            req=req,
            safety=safety,
            budget_remaining_usd=100.0,
            daily_limit_usd=100.0,
        )
        return (
            f"selected_model={decision.selected_model} "
            f"provider={decision.selected_provider} "
            f"complexity={round(decision.complexity_score, 3)} "
            f"reason={decision.reason}"
        )

    @tool
    def complexity_score(prompt: str) -> str:
        """Return the InferOps complexity score (0.0 - 1.0) for a prompt."""
        score = estimate_complexity(prompt, "auto")
        return f"complexity_score={round(score, 3)}"

    return [rag_search, routing_decision, complexity_score]


def run_agent(question: str, model: str | None = None) -> dict[str, Any]:
    """Run the LangChain ReAct-style tool-calling agent on `question`."""

    if not os.getenv("OPENAI_API_KEY"):
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not configured. The agent requires an OpenAI tool-calling model.",
            "answer": None,
            "steps": [],
        }

    try:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.callbacks import BaseCallbackHandler
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        return {
            "ok": False,
            "error": f"LangChain dependencies missing: {exc}. Install langchain, langchain-openai.",
            "answer": None,
            "steps": [],
        }

    class _TokenUsageCallback(BaseCallbackHandler):
        def __init__(self) -> None:
            self.input_tokens = 0
            self.output_tokens = 0

        def on_llm_end(self, response, **kwargs):  # type: ignore[override]
            usage = {}
            try:
                gens = response.generations or []
                if gens and gens[0]:
                    msg = getattr(gens[0][0], "message", None)
                    meta = getattr(msg, "usage_metadata", None) if msg else None
                    if meta:
                        usage = meta
            except Exception:
                usage = {}
            if not usage:
                llm_output = getattr(response, "llm_output", None) or {}
                usage = llm_output.get("token_usage") or {}

            self.input_tokens += int(
                usage.get("input_tokens") or usage.get("prompt_tokens") or 0
            )
            self.output_tokens += int(
                usage.get("output_tokens") or usage.get("completion_tokens") or 0
            )

    usage_cb = _TokenUsageCallback()

    llm = ChatOpenAI(model=model or "gpt-4o-mini", temperature=0)
    tools = _build_tools()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an operations assistant for the InferOps AI gateway. "
                "Answer the user's question. When the question is about runbooks, "
                "policies, or any project-specific knowledge, call `rag_search` first. "
                "When the question is about how a prompt would be routed, call "
                "`routing_decision`. When asked to score complexity of a prompt, "
                "call `complexity_score`. Cite the document name and chunk for "
                "any fact you take from `rag_search`. Be concise.",
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        return_intermediate_steps=True,
        max_iterations=5,
        verbose=False,
    )

    result = executor.invoke({"input": question}, config={"callbacks": [usage_cb]})

    steps: list[dict[str, Any]] = []
    for action, observation in result.get("intermediate_steps", []):
        steps.append(
            {
                "tool": getattr(action, "tool", None),
                "tool_input": getattr(action, "tool_input", None),
                "observation": str(observation)[:4000],
            }
        )

    return {
        "ok": True,
        "answer": result.get("output", ""),
        "model": model or "gpt-4o-mini",
        "tools_used": sorted({s["tool"] for s in steps if s["tool"]}),
        "steps": steps,
        "input_tokens": usage_cb.input_tokens,
        "output_tokens": usage_cb.output_tokens,
    }

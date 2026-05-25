"""Prometheus metrics.

In local Docker Compose Prometheus scrapes /metrics normally.
In Lambda there's nothing scraping, but prometheus_client itself works
fine — we keep the same metric objects so the call-sites in routes_chat,
routes_agent etc. don't need branching. If the library is ever absent
(e.g. trimmed dependency), no-op stubs keep import working.
"""
from __future__ import annotations

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    from fastapi import Response

    PROMETHEUS_AVAILABLE = True

    def metrics_response():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

except ImportError:  # pragma: no cover — defensive fallback
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class _NoOpMetric:  # NOSONAR — intentional stub used only when prometheus_client is unavailable
        def labels(self, *_args, **_kwargs):
            return self

        def inc(self, *_args, **_kwargs):
            return None

        def observe(self, *_args, **_kwargs):
            return None

        def set(self, *_args, **_kwargs):
            return None

    def Counter(*_args, **_kwargs):  # type: ignore[no-redef]  # NOSONAR — shadows prometheus_client.Counter
        return _NoOpMetric()

    def Histogram(*_args, **_kwargs):  # type: ignore[no-redef]  # NOSONAR — shadows prometheus_client.Histogram
        return _NoOpMetric()

    def Gauge(*_args, **_kwargs):  # type: ignore[no-redef]  # NOSONAR — shadows prometheus_client.Gauge
        return _NoOpMetric()

    def generate_latest():  # type: ignore[no-redef]
        return b""

    def metrics_response():
        from fastapi import Response  # local import keeps stub light

        return Response(b"", media_type=CONTENT_TYPE_LATEST)


REQUEST_COUNT = Counter(
    "inferops_requests_total",
    "Total InferOps requests",
    ["model", "provider", "status"],
)

REQUEST_LATENCY = Histogram(
    "inferops_request_latency_ms",
    "InferOps request latency in milliseconds",
    ["model", "provider"],
    buckets=[1, 5, 10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000],
)

REQUEST_COST = Counter(
    "inferops_request_cost_usd_total",
    "Estimated request cost in USD",
    ["model", "provider"],
)

SAFETY_BLOCKS = Counter(
    "inferops_safety_blocks_total",
    "Total safety-blocked requests",
)

FALLBACK_COUNT = Counter(
    "inferops_fallback_total",
    "Total fallback events",
    ["from_provider", "to_provider"],
)

BUDGET_REMAINING = Gauge(
    "inferops_budget_remaining_usd",
    "Remaining user budget in USD",
    ["user_id"],
)

PII_DETECTIONS_TOTAL = Counter(
    "inferops_pii_detections_total",
    "Total requests containing PII",
)

CACHE_HITS_TOTAL = Counter(
    "inferops_cache_hits_total",
    "Total exact Redis cache hits",
)

CACHE_MISSES_TOTAL = Counter(
    "inferops_cache_misses_total",
    "Total Redis cache misses",
)

RAG_QUERIES_TOTAL = Counter(
    "inferops_rag_queries_total",
    "Total RAG retrieval queries",
    ["used"],
)

RAG_RETRIEVED_CHUNKS = Histogram(
    "inferops_rag_retrieved_chunks",
    "Number of chunks retrieved per RAG query",
    buckets=[0, 1, 2, 3, 5, 10],
)

RAG_TOP_SCORE = Histogram(
    "inferops_rag_top_score",
    "Top semantic similarity score for RAG retrieval",
    buckets=[0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0],
)


AGENT_RUNS_TOTAL = Counter(
    "inferops_agent_runs_total",
    "Total LangChain agent runs (POST /v1/agent/run)",
    ["model", "status"],
)

AGENT_LATENCY_MS = Histogram(
    "inferops_agent_latency_ms",
    "Latency of LangChain agent runs in milliseconds",
    ["model"],
    buckets=[100, 250, 500, 1000, 2500, 5000, 10000, 20000, 30000, 60000],
)

AGENT_TOOL_CALLS_TOTAL = Counter(
    "inferops_agent_tool_calls_total",
    "Number of tool invocations made by the LangChain agent",
    ["tool"],
)

AGENT_TOKENS_TOTAL = Counter(
    "inferops_agent_tokens_total",
    "Tokens consumed by the LangChain agent",
    ["kind"],
)

EVAL_RUNS_TOTAL = Counter(
    "inferops_eval_runs_total",
    "Deterministic eval suite executions (POST /v1/evals/run)",
)

EVAL_CASES_TOTAL = Counter(
    "inferops_eval_cases_total",
    "Eval cases executed, partitioned by pass/fail",
    ["result"],
)

EVAL_ROUTING_ACCURACY = Gauge(
    "inferops_eval_routing_accuracy",
    "Routing accuracy of the last deterministic eval run (percent 0-100)",
)

JUDGE_RUNS_TOTAL = Counter(
    "inferops_judge_runs_total",
    "LLM-as-judge eval executions (POST /v1/evals/judge)",
    ["judge_model", "status"],
)

JUDGE_SCORE = Histogram(
    "inferops_judge_score",
    "Per-case LLM-as-judge score (1..5)",
    ["judge_model"],
    buckets=[1, 2, 3, 4, 5],
)

JUDGE_AVG_SCORE = Gauge(
    "inferops_judge_avg_score",
    "Average LLM-as-judge score of the last run",
    ["judge_model"],
)

RAGAS_RUNS_TOTAL = Counter(
    "inferops_ragas_runs_total",
    "RAGAS eval executions (POST /v1/evals/ragas)",
    ["status"],
)

RAGAS_SCORE = Gauge(
    "inferops_ragas_score",
    "Aggregate RAGAS metric scores (0..1) from the last run",
    ["metric"],
)

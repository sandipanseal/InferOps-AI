from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response


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


def metrics_response():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
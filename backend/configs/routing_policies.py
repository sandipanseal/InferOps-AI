LOCAL_MODEL = "llama3.1:8b"
PREMIUM_MODEL = "gpt-4.1"
CHEAP_MODEL = "mock-cheap"

LOCAL_PROVIDER = "ollama"
PREMIUM_PROVIDER = "openai"
CHEAP_PROVIDER = "mock"

BLOCKED_MODEL = "blocked"
BLOCKED_PROVIDER = "none"

LOW_COMPLEXITY_THRESHOLD = 0.55
HIGH_COMPLEXITY_THRESHOLD = 0.65
LOW_BUDGET_RATIO = 0.20

CACHE_MODEL = "redis-cache"
CACHE_PROVIDER = "cache"

ROUTING_REASONS = {
    "blocked": "Request blocked by safety policy.",
    "local_privacy": "Request routed to local model because {reason}.",
    "low_budget": "Daily budget is low; routed to cheapest available model.",
    "quality_premium": "High-complexity quality-optimized request routed to premium model.",
    "quality_local": "Quality-optimized simple or medium request routed to local model instead of mock provider.",
    "latency_fast": "Latency-optimized request routed to fastest configured provider.",
    "cost_low": "Low-complexity task routed to cost-effective model.",
    "balanced_local": "Medium-complexity task routed to local model to balance cost and quality.",
}
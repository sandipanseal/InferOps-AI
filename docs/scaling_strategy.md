# Scaling Strategy

## Local MVP

Use Docker Compose with backend, frontend, Redis, Qdrant, Prometheus, and Grafana.

## Production-style CPU deployment

Use Kubernetes for the gateway and scale it with HPA.

## GPU-ready deployment

Use vLLM or NVIDIA NIM-compatible endpoints behind the same provider abstraction.

Scaling parameters:

- min_replicas
- max_replicas
- target_cpu_utilization
- target_p95_latency_ms
- max_tokens
- timeout_seconds
- queue_max_size
- per-user budget
- per-model rate limits

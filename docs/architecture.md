# Architecture

InferOps AI has two main parts:

1. **InferOps Gateway**: FastAPI backend for safety, routing, budget checks, provider calls, fallback, logging, and metrics.
2. **InferOps Console**: Next.js frontend for operators to inspect requests, model routing, cost, logs, and model status.

## Request lifecycle

```text
User request
  -> PII detection
  -> Prompt injection check
  -> Budget check
  -> Complexity scoring
  -> Model routing
  -> Provider call
  -> Fallback if provider fails
  -> Cost estimation
  -> Request log
  -> Metrics export
  -> Frontend display
```

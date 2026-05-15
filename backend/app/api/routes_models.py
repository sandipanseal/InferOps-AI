from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models")
async def get_models():
    return [
        {
            "name": "mock-cheap",
            "provider": "mock",
            "status": "healthy",
            "cost_tier": "free",
            "deployment": "local",
            "description": "Zero-cost mock provider for development, routing tests, and budget-safe demos.",
        },
        {
            "name": "llama3.1:8b",
            "provider": "ollama",
            "status": "healthy",
            "cost_tier": "low",
            "deployment": "local",
            "description": "Local Ollama model used for privacy-sensitive and PII-containing requests.",
        },
        {
            "name": "gpt-oss:120b-cloud",
            "provider": "ollama_cloud",
            "status": "requires API key",
            "cost_tier": "medium",
            "deployment": "cloud",
            "description": "Ollama Cloud model option for hosted open-model inference without running a local GPU server.",
        },
        {
            "name": "vllm-llama",
            "provider": "vllm",
            "status": "optional",
            "cost_tier": "low",
            "deployment": "gpu-ready",
            "description": "GPU-ready OpenAI-compatible vLLM endpoint for scalable self-hosted inference.",
        },
        {
            "name": "gpt-4.1",
            "provider": "openai",
            "status": "healthy",
            "cost_tier": "premium",
            "deployment": "cloud",
            "description": "Premium model route for high-complexity, quality-optimized requests.",
        },
    ]
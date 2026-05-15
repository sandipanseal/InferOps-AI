from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.vllm_provider import VLLMProvider


def get_provider(provider_name: str):
    providers = {
        "mock": MockProvider(),
        "openai": OpenAIProvider(),
        "ollama": OllamaProvider(),
        "vllm": VLLMProvider(),
    }
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")
    return providers[provider_name]

from app.providers.registry import get_provider
from app.providers.base import ProviderResponse
from app.providers.ollama_cloud import generate_ollama_cloud


FALLBACK_CHAIN = {
    # If OpenAI fails, first try Ollama Cloud, then local Ollama, then mock.
    "openai": [
        ("ollama_cloud", "gpt-oss:120b-cloud"),
        ("ollama", "local-llama"),
        ("mock", "mock-cheap"),
    ],

    # If Ollama Cloud fails, try local Ollama, then mock.
    "ollama_cloud": [
        ("ollama", "local-llama"),
        ("mock", "mock-cheap"),
    ],

    # If local Ollama fails, try mock.
    "ollama": [
        ("mock", "mock-cheap"),
    ],

    # If vLLM fails, try Ollama Cloud, then local Ollama, then mock.
    "vllm": [
        ("ollama_cloud", "gpt-oss:120b-cloud"),
        ("ollama", "local-llama"),
        ("mock", "mock-cheap"),
    ],

    "mock": [],
}


async def call_provider(
    provider_name: str,
    model: str,
    prompt: str,
    max_tokens: int,
) -> ProviderResponse:
    """
    Calls the selected provider.

    Ollama Cloud is handled directly because it may not be registered
    inside the normal provider registry.
    """

    if provider_name == "ollama_cloud":
        return await generate_ollama_cloud(
            prompt=prompt,
            max_output_tokens=max_tokens,
        )

    provider = get_provider(provider_name)

    return await provider.generate(
        prompt,
        model,
        max_tokens=max_tokens,
    )


async def generate_with_fallback(
    provider_name: str,
    model: str,
    prompt: str,
    max_tokens: int,
) -> tuple[ProviderResponse, bool, str | None, str, str]:
    """
    Tries the primary provider first.
    If it fails, tries configured fallback providers.
    If every provider fails, returns a safe static response.
    """

    try:
        response = await call_provider(
            provider_name=provider_name,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
        )

        return response, False, None, provider_name, model

    except Exception as primary_error:
        for fallback_provider, fallback_model in FALLBACK_CHAIN.get(provider_name, []):
            try:
                response = await call_provider(
                    provider_name=fallback_provider,
                    model=fallback_model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                )

                return (
                    response,
                    True,
                    str(primary_error),
                    fallback_provider,
                    fallback_model,
                )

            except Exception:
                continue

        safe_text = (
            "The AI service is temporarily unavailable. "
            "Please try again later."
        )

        response = ProviderResponse(
            text=safe_text,
            input_tokens=max(1, len(prompt) // 4),
            output_tokens=max(1, len(safe_text) // 4),
            raw=None,
        )

        return (
            response,
            True,
            str(primary_error),
            "safe_static",
            "safe_static",
        )
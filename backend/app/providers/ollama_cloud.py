import httpx

from app.config import get_settings
from app.providers.base import ProviderResponse

settings = get_settings()


async def generate_ollama_cloud(
    prompt: str,
    max_output_tokens: int = 512,
) -> ProviderResponse:
    if not settings.ollama_cloud_api_key:
        raise RuntimeError("OLLAMA_CLOUD_API_KEY is not configured.")

    url = f"{settings.ollama_cloud_base_url.rstrip('/')}/api/chat"

    payload = {
        "model": settings.ollama_cloud_model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "options": {
            "num_predict": max_output_tokens,
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.ollama_cloud_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    message = data.get("message", {})
    text = message.get("content") or data.get("response") or ""

    input_tokens = int(data.get("prompt_eval_count") or max(1, len(prompt) // 4))
    output_tokens = int(data.get("eval_count") or max(1, len(text) // 4))

    return ProviderResponse(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        provider="ollama_cloud",
        model=settings.ollama_cloud_model,
    )
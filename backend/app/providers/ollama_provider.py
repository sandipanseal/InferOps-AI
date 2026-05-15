import httpx
from app.config import get_settings
from app.providers.base import LLMProvider, ProviderResponse


class OllamaProvider(LLMProvider):
    name = "ollama"

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> ProviderResponse:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            res.raise_for_status()
            data = res.json()

        text = data.get("response", "")
        return ProviderResponse(
            text=text,
            input_tokens=max(1, len(prompt) // 4),
            output_tokens=max(1, len(text) // 4),
            raw=data,
        )

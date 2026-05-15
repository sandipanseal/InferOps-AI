import httpx
from app.config import get_settings
from app.providers.base import LLMProvider, ProviderResponse


class VLLMProvider(LLMProvider):
    name = "vllm"

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> ProviderResponse:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                f"{settings.vllm_base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
            )
            res.raise_for_status()
            data = res.json()

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return ProviderResponse(
            text=text,
            input_tokens=usage.get("prompt_tokens", max(1, len(prompt) // 4)),
            output_tokens=usage.get("completion_tokens", max(1, len(text) // 4)),
            raw=data,
        )

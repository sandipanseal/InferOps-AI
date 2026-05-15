import os
import httpx
from app.providers.base import LLMProvider, ProviderResponse


class OpenAIProvider(LLMProvider):
    name = "openai"

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> ProviderResponse:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
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

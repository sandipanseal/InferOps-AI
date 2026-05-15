from dataclasses import dataclass


@dataclass
class ProviderResponse:
    text: str
    input_tokens: int
    output_tokens: int
    raw: dict | None = None


class LLMProvider:
    name: str = "base"

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> ProviderResponse:
        raise NotImplementedError

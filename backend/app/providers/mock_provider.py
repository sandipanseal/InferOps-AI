from app.providers.base import LLMProvider, ProviderResponse


class MockProvider(LLMProvider):
    name = "mock"

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> ProviderResponse:
        user_part = prompt

        if "Latest user message:" in prompt:
            user_part = prompt.split("Latest user message:", 1)[-1].strip()

        if "User request:" in user_part:
            user_part = user_part.split("User request:", 1)[-1].strip()

        lower = user_part.lower()

        if "classify" in lower and "charged" in lower:
            text = (
                "Classification: billing\n\n"
                "Reason: The user mentions being charged twice, which is a payment/subscription issue."
            )
        elif "summarize" in lower:
            text = (
                "Summary:\n\n"
                "- The customer reports an issue that needs support attention.\n"
                "- The request was handled through the zero-cost mock provider."
            )
        else:
            text = (
                f"[Mock response from {model}]\n\n"
                "This request was processed through the zero-cost mock provider.\n\n"
                f"Input preview: {user_part[:180]}"
            )

        return ProviderResponse(
            text=text,
            input_tokens=max(1, len(prompt) // 4),
            output_tokens=max(1, len(text) // 4),
            raw={"provider": self.name},
        )
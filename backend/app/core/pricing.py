MODEL_PRICES = {
    "mock-cheap": {"input": 0.0, "output": 0.0},
    "local-llama": {"input": 0.0001, "output": 0.0001},
    "llama3.1:8b": {"input": 0.0001, "output": 0.0001},
    "vllm-llama": {"input": 0.0002, "output": 0.0002},
    "gpt-4.1": {"input": 0.002, "output": 0.008},
    "openai-premium": {"input": 0.002, "output": 0.008},
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = MODEL_PRICES.get(model, MODEL_PRICES["mock-cheap"])
    cost = (input_tokens / 1000) * price["input"] + (output_tokens / 1000) * price["output"]
    return round(cost, 6)

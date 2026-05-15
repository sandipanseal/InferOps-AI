from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = "demo_user"
    input: str
    task_type: str = "auto"
    priority: str = Field(default="cost_optimized", pattern="^(cost_optimized|quality_optimized|latency_optimized)$")
    privacy: str = Field(default="normal", pattern="^(normal|sensitive|local_only)$")
    max_output_tokens: int = 512


class SafetyResult(BaseModel):
    contains_pii: bool = False
    pii_redacted: bool = False
    prompt_injection_risk: str = "low"
    blocked: bool = False
    reasons: list[str] = []


class RoutingDecision(BaseModel):
    selected_model: str
    selected_provider: str
    reason: str
    complexity_score: float
    budget_remaining_usd: float


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class FallbackInfo(BaseModel):
    used: bool = False
    reason: str | None = None
    fallback_model: str | None = None


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    selected_model: str
    selected_provider: str
    routing_reason: str
    latency_ms: int
    estimated_cost_usd: float
    tokens: TokenUsage
    safety: SafetyResult
    fallback: FallbackInfo
    trace_id: str
    created_at: datetime

class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class ChatConversationRequest(BaseModel):
    user_id: str = "demo_user"
    conversation_id: str | None = None
    messages: list[ChatMessage]
    task_type: str = "auto"
    priority: str = Field(default="cost_optimized", pattern="^(cost_optimized|quality_optimized|latency_optimized)$")
    privacy: str = Field(default="normal", pattern="^(normal|sensitive|local_only)$")
    max_output_tokens: int = 512


class ChatConversationResponse(BaseModel):
    conversation_id: str
    request_id: str
    assistant_message: ChatMessage
    selected_model: str
    selected_provider: str
    routing_reason: str
    latency_ms: int
    estimated_cost_usd: float
    tokens: TokenUsage
    safety: SafetyResult
    fallback: FallbackInfo
    trace_id: str
    created_at: datetime

from app.core.complexity import estimate_complexity
from app.schemas import ChatRequest, SafetyResult, RoutingDecision

from configs.routing_policies import (
    LOCAL_MODEL,
    PREMIUM_MODEL,
    CHEAP_MODEL,
    LOCAL_PROVIDER,
    PREMIUM_PROVIDER,
    CHEAP_PROVIDER,
    BLOCKED_MODEL,
    BLOCKED_PROVIDER,
    LOW_COMPLEXITY_THRESHOLD,
    HIGH_COMPLEXITY_THRESHOLD,
    LOW_BUDGET_RATIO,
    ROUTING_REASONS,
)


# Ollama Cloud route
OLLAMA_CLOUD_MODEL = "gpt-oss:120b-cloud"
OLLAMA_CLOUD_PROVIDER = "ollama_cloud"


def route_request(
    req: ChatRequest,
    safety: SafetyResult,
    budget_remaining_usd: float,
    daily_limit_usd: float,
) -> RoutingDecision:
    complexity = estimate_complexity(req.input, req.task_type)

    if safety.blocked:
        return RoutingDecision(
            selected_model=BLOCKED_MODEL,
            selected_provider=BLOCKED_PROVIDER,
            reason=ROUTING_REASONS["blocked"],
            complexity_score=complexity,
            budget_remaining_usd=budget_remaining_usd,
        )

    # Sensitive data must stay local.
    if req.privacy in {"local_only", "sensitive"} or safety.contains_pii:
        reason_parts = []

        if req.privacy == "local_only":
            reason_parts.append("local-only privacy mode was selected")

        if req.privacy == "sensitive":
            reason_parts.append("sensitive privacy mode was selected")

        if safety.contains_pii:
            reason_parts.append("PII was detected")

        reason = ROUTING_REASONS["local_privacy"].format(
            reason=", ".join(reason_parts)
        )

        return RoutingDecision(
            selected_model=LOCAL_MODEL,
            selected_provider=LOCAL_PROVIDER,
            reason=reason,
            complexity_score=complexity,
            budget_remaining_usd=budget_remaining_usd,
        )

    budget_ratio = budget_remaining_usd / daily_limit_usd if daily_limit_usd > 0 else 0

    # Very low budget: keep cheapest route.
    if budget_ratio < LOW_BUDGET_RATIO:
        return RoutingDecision(
            selected_model=CHEAP_MODEL,
            selected_provider=CHEAP_PROVIDER,
            reason=ROUTING_REASONS["low_budget"],
            complexity_score=complexity,
            budget_remaining_usd=budget_remaining_usd,
        )

    # Quality mode:
    # - very high complexity goes to OpenAI premium
    # - medium/high complexity goes to Ollama Cloud
    # - lower complexity goes to local Ollama
    if req.priority == "quality_optimized":
        if complexity >= HIGH_COMPLEXITY_THRESHOLD:
            return RoutingDecision(
                selected_model=PREMIUM_MODEL,
                selected_provider=PREMIUM_PROVIDER,
                reason=ROUTING_REASONS["quality_premium"],
                complexity_score=complexity,
                budget_remaining_usd=budget_remaining_usd,
            )

        if complexity >= 0.55:
            return RoutingDecision(
                selected_model=OLLAMA_CLOUD_MODEL,
                selected_provider=OLLAMA_CLOUD_PROVIDER,
                reason=(
                    "Quality-optimized request routed to Ollama Cloud because "
                    "the task is moderately complex and does not require the premium OpenAI route."
                ),
                complexity_score=complexity,
                budget_remaining_usd=budget_remaining_usd,
            )

        return RoutingDecision(
            selected_model=LOCAL_MODEL,
            selected_provider=LOCAL_PROVIDER,
            reason=ROUTING_REASONS["quality_local"],
            complexity_score=complexity,
            budget_remaining_usd=budget_remaining_usd,
        )

    # Latency mode:
    # Keep fast/cheap route for simple requests.
    # Use Ollama Cloud for non-trivial latency-sensitive tasks when privacy allows cloud.
    if req.priority == "latency_optimized":
        if complexity >= 0.55:
            return RoutingDecision(
                selected_model=OLLAMA_CLOUD_MODEL,
                selected_provider=OLLAMA_CLOUD_PROVIDER,
                reason=(
                    "Latency-optimized request routed to Ollama Cloud because "
                    "the task is non-trivial and cloud inference is available."
                ),
                complexity_score=complexity,
                budget_remaining_usd=budget_remaining_usd,
            )

        return RoutingDecision(
            selected_model=CHEAP_MODEL,
            selected_provider=CHEAP_PROVIDER,
            reason=ROUTING_REASONS["latency_fast"],
            complexity_score=complexity,
            budget_remaining_usd=budget_remaining_usd,
        )

    # Cost mode:
    # Very simple tasks go to mock-cheap.
    # Medium tasks go to local Ollama.
    # Higher complexity tasks can use Ollama Cloud as a cheaper cloud option than OpenAI.
    if req.priority == "cost_optimized":
        if complexity < LOW_COMPLEXITY_THRESHOLD:
            return RoutingDecision(
                selected_model=CHEAP_MODEL,
                selected_provider=CHEAP_PROVIDER,
                reason=ROUTING_REASONS["cost_low"],
                complexity_score=complexity,
                budget_remaining_usd=budget_remaining_usd,
            )

        if complexity >= 0.70:
            return RoutingDecision(
                selected_model=OLLAMA_CLOUD_MODEL,
                selected_provider=OLLAMA_CLOUD_PROVIDER,
                reason=(
                    "Cost-optimized request routed to Ollama Cloud because "
                    "the task is complex enough to need a stronger model while avoiding premium OpenAI cost."
                ),
                complexity_score=complexity,
                budget_remaining_usd=budget_remaining_usd,
            )

    return RoutingDecision(
        selected_model=LOCAL_MODEL,
        selected_provider=LOCAL_PROVIDER,
        reason=ROUTING_REASONS["balanced_local"],
        complexity_score=complexity,
        budget_remaining_usd=budget_remaining_usd,
    )
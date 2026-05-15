import json
import asyncio
import httpx
from pathlib import Path


async def run():
    base_url = "http://localhost:8000"
    path = Path(__file__).parent / "routing_eval.jsonl"
    total = 0
    passed = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            case = json.loads(line)
            payload = {
                "user_id": "eval_user",
                "input": case["input"],
                "task_type": case.get("task_type", "auto"),
                "priority": case.get("priority", "cost_optimized"),
                "privacy": case.get("privacy", "normal"),
            }
            res = await client.post(f"{base_url}/v1/chat", json=payload)
            res.raise_for_status()
            data = res.json()
            total += 1
            ok = True
            if "expected_model" in case:
                ok = ok and data["selected_model"] == case["expected_model"]
            if "expected_provider" in case:
                ok = ok and data["selected_provider"] == case["expected_provider"]
            passed += int(ok)
            print({"case": case["input"][:50], "passed": ok, "actual_model": data["selected_model"], "provider": data["selected_provider"]})

    print(f"Routing eval accuracy: {passed}/{total} = {passed/total:.2%}")


if __name__ == "__main__":
    asyncio.run(run())

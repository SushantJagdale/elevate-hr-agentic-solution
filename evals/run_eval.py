"""Automated Evaluation Runner."""

import json
import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agent.orchestrator import hr_orchestrator

EVAL_DIR = Path(__file__).resolve().parent
DATASET_PATH = EVAL_DIR / "golden_dataset.json"


def run_evaluation():
    print("=" * 70)
    print("🧪 Running Enterprise HR Assistant Evaluation Benchmark")
    print(f"   Dataset: {DATASET_PATH.name}")
    print("=" * 70)

    if not DATASET_PATH.exists():
        print(f"❌ Error: Dataset {DATASET_PATH} not found.")
        return

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total = len(dataset)
    passed = 0
    results = []

    for item in dataset:
        e_id = item["id"]
        category = item["category"]
        query = item["query"]
        expected_tool = item.get("expected_tool")
        expected_keywords = item.get("expected_keywords", [])
        should_refuse = item.get("should_refuse", False)

        start_time = time.time()
        res = hr_orchestrator.run_turn(
            session_id=f"eval_session_{e_id}",
            user_prompt=query,
        )
        latency = int((time.time() - start_time) * 1000)

        response_text = res.get("response", "")
        executed_tools = [t["tool_name"] for t in res.get("tool_calls", [])]

        # Criteria 1: Tool Calling
        tool_pass = True
        if expected_tool:
            tool_pass = expected_tool in executed_tools
        elif expected_tool is None and len(executed_tools) > 0 and should_refuse:
            tool_pass = False

        # Criteria 2: Keyword Coverage
        keyword_pass = all(
            kw.lower() in response_text.lower() for kw in expected_keywords
        )

        test_passed = tool_pass and (keyword_pass or len(expected_keywords) == 0)

        if test_passed:
            passed += 1
            status_icon = "✅ PASS"
        else:
            status_icon = "❌ FAIL"

        print(f"\n{status_icon} [{e_id}] Category: {category} ({latency}ms)")
        print(f"   Query: {query}")
        print(f"   Executed Tools: {executed_tools}")
        if not test_passed:
            print(f"   Expected Tool: {expected_tool} (Matched: {tool_pass})")
            print(f"   Expected Keywords: {expected_keywords} (Matched: {keyword_pass})")

        results.append({
            "id": e_id,
            "category": category,
            "passed": test_passed,
            "latency_ms": latency,
            "tool_pass": tool_pass,
            "keyword_pass": keyword_pass,
        })

    accuracy = (passed / total) * 100
    print("\n" + "=" * 70)
    print(f"📊 Evaluation Summary: {passed}/{total} Passed ({accuracy:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()

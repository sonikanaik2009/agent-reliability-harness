import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from evaluator import (
    INPUT_PRICE_PER_MILLION,
    OUTPUT_PRICE_PER_MILLION,
    evaluate_case,
)
RESULTS_DIR = Path("results")
TEST_CASES_FILE = Path("test_cases.json")
FAILURE_DESCRIPTIONS = {
    "search_failure": (
        "The web-search service raises an exception. "
        "The agent must handle the failure without producing an unsupported answer."
    ),
    "empty_search": (
        "The search service returns no sources. "
        "The agent must avoid inventing citations or claiming that research succeeded."
    ),
    "invalid_citation": (
        "The generated answer cites a source ID that was never retrieved. Citation validation should reject the answer."
    ),
    "fetch_failure": (
        "A webpage cannot be retrieved. The agent should still be able to use available search results when appropriate."
    ),
    "empty_fetch": (
        "Page retrieval succeeds technically but returns no usable content."
    ),
    "unknown_url": (
        "The agent requests a URL that was not discovered by its search tool."
    ),
    "empty_input": (
        "The user provides no meaningful research question."
    ),
}

def percent(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round(
        numerator / denominator * 100,
        2,
    )

def calculate_metrics(results):
    total = len(results)
    passed = sum(
        result["passed"]
        for result in results
    )
    answer_expected = [
        result
        for result in results
        if result["expected"] == "answer"
    ]
    successful_answers = [
        result
        for result in answer_expected
        if result["passed"]
        and result["actual"] == "answer"
    ]
    total_estimated_cost = sum(
        result["estimated_cost_usd"]
        for result in results
    )
    if successful_answers:
        cost_per_success = (
            total_estimated_cost
            / len(successful_answers)
        )
    else:
        cost_per_success = None
    return {
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": total - passed,
        "test_pass_rate_percent": percent(
            passed,
            total,
        ),
        "answer_expected_tests": len(
            answer_expected
        ),
        "successful_answers": len(
            successful_answers
        ),
        "answer_success_rate_percent": percent(
            len(successful_answers),
            len(answer_expected),
        ),
        "total_estimated_cost_usd": round(
            total_estimated_cost,
            8,
        ),
        "estimated_cost_per_success_usd": (
            round(cost_per_success, 8)
            if cost_per_success is not None
            else None
        ),
        "total_duration_seconds": round(
            sum(
                result["duration_seconds"]
                for result in results
            ),
            4,
        ),
        "total_tool_calls": sum(
            result["tool_calls"]
            for result in results
        ),
    }

def analyze_failure_modes(results):
    """
    Count the injected adverse conditions.
    These counts describe simulated failure
    scenarios, not observed production incidents.
    """
    counts = Counter(
        result["scenario"]
        for result in results
        if result["scenario"] != "normal"
    )
    return counts.most_common(3)

def generate_report(results, metrics):
    lines = []
    lines.append("# Agent Reliability Evaluation Report")
    lines.append("")
    lines.append(
        f"Generated: {datetime.now(timezone.utc).isoformat()}"
    )
    lines.append("")
    lines.append("## 1. Evaluation methodology")
    lines.append("")
    lines.append(
        "This evaluation executes the research agent's real orchestration logic while replacing external Gemini and Tavily calls with deterministic test responses."
    )
    lines.append("")
    lines.append(
        "The results measure behavior under the specified test scenarios. They are not a measurement of live production accuracy."
    )
    lines.append("")

    lines.append("## 2. Exact definition of success")
    lines.append("")
    lines.append(
        "**Test pass:** The actual outcome matches the expected outcome defined in the test case, answer-expected cases return nonempty answers and sources, and tool calls stay within the configured step limit."
    )
    lines.append("")
    lines.append(
        "**Answer success:** An answer-expected test passes and returns an answer with at least one collected source."
    )
    lines.append("")
    lines.append(
        "An expected error can count as a passed test, but it does not count as a successful answer."
    )
    lines.append("")

    lines.append("## 3. Results")
    lines.append("")
    lines.append(
        f"- Total evaluation cases: "
        f"{metrics['total_tests']}"
    )
    lines.append(
        f"- Passed cases: "
        f"{metrics['passed_tests']}"
    )
    lines.append(
        f"- Failed cases: "
        f"{metrics['failed_tests']}"
    )
    lines.append(
        f"- Test pass rate: "
        f"{metrics['test_pass_rate_percent']}%"
    )
    lines.append(
        f"- Answer success rate: "
        f"{metrics['answer_success_rate_percent']}%"
    )
    lines.append(
        f"- Total tool calls: "
        f"{metrics['total_tool_calls']}"
    )
    lines.append("")

    lines.append("## 4. Cost per successful run")
    lines.append("")
    lines.append(
        f"- Estimated input-token rate: "
        f"${INPUT_PRICE_PER_MILLION} "
        f"per million tokens"
    )
    lines.append(
        f"- Estimated output-token rate: "
        f"${OUTPUT_PRICE_PER_MILLION} "
        f"per million tokens"
    )
    lines.append(
        "- Token estimate: approximately 4 characters per token"
    )
    lines.append(
        f"- Total estimated equivalent cost: "
        f"${metrics['total_estimated_cost_usd']:.8f}"
    )

    cost = metrics[
        "estimated_cost_per_success_usd"
    ]

    if cost is None:
        lines.append(
            "- Estimated cost per successful answer: "
            "N/A (no successful answers)"
        )
    else:
        lines.append(
            f"- Estimated cost per successful answer: "
            f"${cost:.8f}"
        )

    lines.append("")
    lines.append(
        "**Important:** The automated evaluation uses mocked API calls. These values are modeled equivalent costs, not actual charges. Pricing assumptions are configurable and should not be treated as current provider pricing."
    )
    lines.append("")
    lines.append(
        "Cost per successful answer is calculated as total estimated cost across all evaluated cases divided by the number of successful answers. This includes the modeled cost of unsuccessful attempts."
    )
    lines.append("")

    lines.append("## 5. Top three injected failure modes")
    lines.append("")
    lines.append(
        "The following ranking describes the most frequently represented adverse conditions in this test suite. It does not claim these are the most common failures in real-world usage."
    )
    lines.append("")
    top_three = analyze_failure_modes(results)
    for index, (scenario, count) in enumerate(
        top_three,
        start=1,
    ):
        description = FAILURE_DESCRIPTIONS.get(
            scenario,
            "An evaluated edge case.",
        )
        lines.append(
            f"### {index}. "
            f"{scenario.replace('_', ' ').title()}"
        )
        lines.append("")
        lines.append(
            f"Cases in suite: {count}"
        )
        lines.append("")
        lines.append(description)
        lines.append("")
    lines.append("## 6. Individual test results")
    lines.append("")
    lines.append(
        "| ID | Test | Expected | Actual | Pass |"
    )
    lines.append(
        "|---|---|---|---|---|"
    )
    for result in results:
        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )
        lines.append(
            f"| {result['id']} "
            f"| {result['name']} "
            f"| {result['expected']} "
            f"| {result['actual']} "
            f"| {status} |"
        )
    lines.append("")
    lines.append("## 7. Failed test details")
    lines.append("")
    failed = [
        result
        for result in results
        if not result["passed"]
    ]
    if not failed:
        lines.append(
            "No test failures were observed in this evaluation run."
        )
    else:
        for result in failed:
            lines.append(
                f"### {result['id']}: "
                f"{result['name']}"
            )
            lines.append("")
            lines.append(
                f"- Expected: {result['expected']}"
            )
            lines.append(
                f"- Actual: {result['actual']}"
            )
            lines.append(
                f"- Error: {result['error']}"
            )
            lines.append("")
    lines.append("## 8. Limitations")
    lines.append("")
    lines.append(
        "- Mocked tests do not verify factual correctness of live model responses."
    )
    lines.append(
        "- A valid citation ID does not prove that the cited source supports a claim."
    )
    lines.append(
        "- Modeled token usage is approximate."
    )
    lines.append(
        "- Simulated failures do not establish real-world failure frequencies."
    )
    lines.append(
        "- Some cases intentionally repeat a failure mechanism with different inputs."
    )
    lines.append("")
    return "\n".join(lines)

def main():
    if not TEST_CASES_FILE.exists():
        raise FileNotFoundError(
            "test_cases.json is missing. "
            "Run: python create_test_cases.py"
        )
    test_cases = json.loads(
        TEST_CASES_FILE.read_text(
            encoding="utf-8"
        )
    )
    if len(test_cases) < 20:
        raise ValueError(
            "The evaluation suite must contain at least 20 cases."
        )
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    results = []
    print("\nRunning Agent Reliability Evaluation\n")
    for test_case in test_cases:
        result = evaluate_case(test_case)
        results.append(result)
        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )
        print(
            f"{result['id']} | "
            f"{status} | "
            f"{result['name']}"
        )
    metrics = calculate_metrics(results)
    json_path = (
        RESULTS_DIR / "evaluation_results.json"
    )
    json_path.write_text(
        json.dumps(
            {
                "metrics": metrics,
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report_path = (
        RESULTS_DIR / "evaluation_report.md"
    )
    report_path.write_text(
        generate_report(results, metrics),
        encoding="utf-8",
    )
    print("\nEvaluation complete.")
    print(
        f"Test pass rate: "
        f"{metrics['test_pass_rate_percent']}%"
    )
    print(
        f"Answer success rate: "
        f"{metrics['answer_success_rate_percent']}%"
    )
    print(
        f"Reports saved in: {RESULTS_DIR.resolve()}"
    )

if __name__ == "__main__":
    main()
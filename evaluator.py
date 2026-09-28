import json
import math
import time
from unittest.mock import patch
from target_agent import agent

INPUT_PRICE_PER_MILLION = 0.10
OUTPUT_PRICE_PER_MILLION = 0.40

def estimate_tokens(text):
    """
    Approximate tokens from text length.
    This uses a rough 4-characters-per-token assumption.
    It is not an exact tokenizer.
    """
    return math.ceil(len(str(text)) / 4)

def estimate_cost(input_tokens, output_tokens):
    """
    Calculate an estimated equivalent API cost in USD.
    """
    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION
    return input_cost + output_cost

def make_search_results():
    """
    Return deterministic search results.
    These URLs are test fixtures, not live webpages.
    """
    return [
        {
            "id": 1,
            "title": "Example Research Source",
            "url": "https://example.com/source-1",
            "content": (
                "This example source contains information used to test the research agent."),
        },
        {
            "id": 2,
            "title": "Additional Research Source",
            "url": "https://example.com/source-2",
            "content": (
                "This additional source provides more information for evaluation."),
        },
    ]

def evaluate_case(test_case):
    """
    Run one evaluation case against the real research()
    function while mocking external API calls.
    """
    decisions = list(test_case["decisions"])
    scenario = test_case["scenario"]
    decision_index = 0
    input_tokens = 0
    output_tokens = 0
    gemini_calls = 0
    search_calls = 0
    fetch_calls = 0

    def fake_gemini(prompt):
        nonlocal decision_index
        nonlocal input_tokens
        nonlocal output_tokens
        nonlocal gemini_calls
        gemini_calls += 1
        input_tokens += estimate_tokens(prompt)
        if decision_index < len(decisions):
            response = json.dumps(decisions[decision_index])
            decision_index += 1
        else:
            response = test_case["final_answer"]
        output_tokens += estimate_tokens(response)
        return response
    
    def fake_search(query, *args, **kwargs):
        nonlocal search_calls
        search_calls += 1
        if scenario == "search_failure":
            raise RuntimeError("Simulated search API failure")
        if scenario == "empty_search":
            return []
        return make_search_results()

    def fake_fetch(url, *args, **kwargs):
        nonlocal fetch_calls
        fetch_calls += 1
        if scenario == "fetch_failure":
            raise RuntimeError("Simulated webpage retrieval failure")
        if scenario == "empty_fetch":
            return ""
        return ("This is the complete simulated page content for a previously discovered research source.")
    started = time.perf_counter()
    actual_outcome = None
    error_message = None
    answer_text = None
    sources = []
    try:
        with (
            patch.object(
                agent,
                "ask_gemini",
                side_effect=fake_gemini,
            ),
            patch.object(
                agent,
                "search_web",
                side_effect=fake_search,
            ),
            patch.object(
                agent,
                "fetch_page",
                side_effect=fake_fetch,
            ),
        ):
            answer_text, sources = agent.research(
                test_case["question"]
            )
        actual_outcome = "answer"
    except Exception as error:
        actual_outcome = "error"
        error_message = str(error)
    elapsed = time.perf_counter() - started
    expected_outcome = test_case["expected"]
    passed = actual_outcome == expected_outcome
    expected_error_text = {
        "empty_input": "question",
        "search_failure": "usable web sources",
        "empty_search": "usable web sources",
        "invalid_citation": "invalid",
    }
    if expected_outcome == "error" and passed:
        required_text = expected_error_text.get(scenario)
        if required_text:
            passed = (
                error_message is not None
                and required_text.lower()
                in error_message.lower()
            )

    if expected_outcome == "answer" and passed:
        passed = bool(
            answer_text
            and str(answer_text).strip()
            and sources
        )

        if passed:
            try:
                agent.validate_citations(
                    answer_text,
                    sources,
                )
            except Exception:
                passed = False
                
    max_steps = getattr(agent, "MAX_STEPS", 3)
    tool_calls = search_calls + fetch_calls
    within_step_limit = tool_calls <= max_steps
    if not within_step_limit:
        passed = False
    estimated_cost = estimate_cost(
        input_tokens,
        output_tokens,
    )

    return {
        "id": test_case["id"],
        "name": test_case["name"],
        "scenario": scenario,
        "expected": expected_outcome,
        "actual": actual_outcome,
        "passed": bool(passed),
        "duration_seconds": round(elapsed, 4),
        "gemini_calls": gemini_calls,
        "search_calls": search_calls,
        "fetch_calls": fetch_calls,
        "tool_calls": tool_calls,
        "within_step_limit": within_step_limit,
        "source_count": len(sources),
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_cost_usd": round(
            estimated_cost,
            8,
        ),
        "error": error_message,
    }
import json
from pathlib import Path
def make_case(
    case_id,
    name,
    question,
    decisions,
    expected,
    scenario="normal",
    final_answer="This is a source-grounded answer [1].",
):
    return {
        "id": case_id,
        "name": name,
        "question": question,
        "decisions": decisions,
        "expected": expected,
        "scenario": scenario,
        "final_answer": final_answer,
    }


def search(query="test research question"):
    return {"action": "search", "query": query}


def fetch(url="https://example.com/source-1"):
    return {"action": "fetch", "url": url}


def answer():
    return {"action": "answer"}


cases = []

# 1–8: Normal research behavior

for number in range(1, 9):
    cases.append(
        make_case(
            case_id=f"TC{number:02d}",
            name=f"Normal research question {number}",
            question=f"Explain research topic {number}.",
            decisions=[search(f"research topic {number}"), answer()],
            expected="answer",
        )
    )

# 9–12: Page retrieval

for number in range(9, 13):
    cases.append(
        make_case(
            case_id=f"TC{number:02d}",
            name=f"Research with page fetch {number}",
            question=f"Explain topic {number} in detail.",
            decisions=[
                search(f"topic {number}"),
                fetch(),
                answer(),
            ],
            expected="answer",
        )
    )

# 13–15: Empty input

for number, question in enumerate(["", " ", "\n\t"], start=13):
    cases.append(
        make_case(
            case_id=f"TC{number:02d}",
            name=f"Empty input {number}",
            question=question,
            decisions=[],
            expected="error",
            scenario="empty_input",
        )
    )

# 16–18: Search tool failures

for number in range(16, 19):
    cases.append(
        make_case(
            case_id=f"TC{number:02d}",
            name=f"Search API failure {number}",
            question=f"Research topic {number}.",
            decisions=[
                search("first attempt"),
                search("second attempt"),
                search("third attempt"),
            ],
            expected="error",
            scenario="search_failure",
        )
    )

# 19–20: Search returns no results

for number in range(19, 21):
    cases.append(
        make_case(
            case_id=f"TC{number:02d}",
            name=f"No search results {number}",
            question=f"Research obscure topic {number}.",
            decisions=[
                search("first attempt"),
                search("second attempt"),
                search("third attempt"),
            ],
            expected="error",
            scenario="empty_search",
        )
    )

# 21: Invalid citation

cases.append(
    make_case(
        case_id="TC21",
        name="Invalid citation number",
        question="Explain a topic.",
        decisions=[search(), answer()],
        expected="error",
        scenario="invalid_citation",
        final_answer="This answer refers to a nonexistent source [999].",
    )
)

# 22: Fetch fails, but search results remain usable

cases.append(
    make_case(
        case_id="TC22",
        name="Page fetch raises an error",
        question="Explain a topic using available sources.",
        decisions=[search(), fetch(), answer()],
        expected="answer",
        scenario="fetch_failure",
    )
)

# 23: Fetch returns empty content

cases.append(
    make_case(
        case_id="TC23",
        name="Page fetch returns empty content",
        question="Explain a topic using available sources.",
        decisions=[search(), fetch(), answer()],
        expected="answer",
        scenario="empty_fetch",
    )
)

# 24: Agent attempts an unknown URL

cases.append(
    make_case(
        case_id="TC24",
        name="Agent requests an unknown source URL",
        question="Explain a topic.",
        decisions=[
            search(),
            fetch("https://unknown.example/not-discovered"),
            answer(),
        ],
        expected="answer",
        scenario="unknown_url",
    )
)

assert len(cases) == 24

output = Path("test_cases.json")
output.write_text(
    json.dumps(cases, indent=2),
    encoding="utf-8",
)

print(f"Created {len(cases)} evaluation cases in {output}")
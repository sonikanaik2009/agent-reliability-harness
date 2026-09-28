# Agent Reliability Evaluation Report

Generated: 2026-09-28T16:58:27.681994+00:00

## 1. Evaluation methodology

This evaluation executes the research agent's real orchestration logic while replacing external Gemini and Tavily calls with deterministic test responses.

The results measure behavior under the specified test scenarios. They are not a measurement of live production accuracy.

## 2. Exact definition of success

**Test pass:** The actual outcome matches the expected outcome defined in the test case, answer-expected cases return nonempty answers and sources, and tool calls stay within the configured step limit.

**Answer success:** An answer-expected test passes and returns an answer with at least one collected source.

An expected error can count as a passed test, but it does not count as a successful answer.

## 3. Results

- Total evaluation cases: 24
- Passed cases: 24
- Failed cases: 0
- Test pass rate: 100.0%
- Answer success rate: 100.0%
- Total tool calls: 37

## 4. Cost per successful run

- Estimated input-token rate: $0.1 per million tokens
- Estimated output-token rate: $0.4 per million tokens
- Token estimate: approximately 4 characters per token
- Total estimated equivalent cost: $0.00312660
- Estimated cost per successful answer: $0.00020844

**Important:** The automated evaluation uses mocked API calls. These values are modeled equivalent costs, not actual charges. Pricing assumptions are configurable and should not be treated as current provider pricing.

Cost per successful answer is calculated as total estimated cost across all evaluated cases divided by the number of successful answers. This includes the modeled cost of unsuccessful attempts.

## 5. Top three injected failure modes

The following ranking describes the most frequently represented adverse conditions in this test suite. It does not claim these are the most common failures in real-world usage.

### 1. Empty Input

Cases in suite: 3

The user provides no meaningful research question.

### 2. Search Failure

Cases in suite: 3

The web-search service raises an exception. The agent must handle the failure without producing an unsupported answer.

### 3. Empty Search

Cases in suite: 2

The search service returns no sources. The agent must avoid inventing citations or claiming that research succeeded.

## 6. Individual test results

| ID | Test | Expected | Actual | Pass |
|---|---|---|---|---|
| TC01 | Normal research question 1 | answer | answer | PASS |
| TC02 | Normal research question 2 | answer | answer | PASS |
| TC03 | Normal research question 3 | answer | answer | PASS |
| TC04 | Normal research question 4 | answer | answer | PASS |
| TC05 | Normal research question 5 | answer | answer | PASS |
| TC06 | Normal research question 6 | answer | answer | PASS |
| TC07 | Normal research question 7 | answer | answer | PASS |
| TC08 | Normal research question 8 | answer | answer | PASS |
| TC09 | Research with page fetch 9 | answer | answer | PASS |
| TC10 | Research with page fetch 10 | answer | answer | PASS |
| TC11 | Research with page fetch 11 | answer | answer | PASS |
| TC12 | Research with page fetch 12 | answer | answer | PASS |
| TC13 | Empty input 13 | error | error | PASS |
| TC14 | Empty input 14 | error | error | PASS |
| TC15 | Empty input 15 | error | error | PASS |
| TC16 | Search API failure 16 | error | error | PASS |
| TC17 | Search API failure 17 | error | error | PASS |
| TC18 | Search API failure 18 | error | error | PASS |
| TC19 | No search results 19 | error | error | PASS |
| TC20 | No search results 20 | error | error | PASS |
| TC21 | Invalid citation number | error | error | PASS |
| TC22 | Page fetch raises an error | answer | answer | PASS |
| TC23 | Page fetch returns empty content | answer | answer | PASS |
| TC24 | Agent requests an unknown source URL | answer | answer | PASS |

## 7. Failed test details

No test failures were observed in this evaluation run.
## 8. Limitations

- Mocked tests do not verify factual correctness of live model responses.
- A valid citation ID does not prove that the cited source supports a claim.
- Modeled token usage is approximate.
- Simulated failures do not establish real-world failure frequencies.
- Some cases intentionally repeat a failure mechanism with different inputs.

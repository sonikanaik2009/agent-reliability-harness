# Agent Reliability Harness

I built this project to evaluate how reliably an AI research agent behaves across normal requests, edge cases, and tool failures.

Instead of testing the agent with only a few successful questions, I wanted a repeatable way to check what happens when search fails, a webpage returns no content, or the model produces an invalid citation.

The harness evaluates the research agent I built in my earlier Tool-Using Research Agent project.

## What the project does

The harness:
- Runs 24 predefined evaluation cases.
- Tests the agent's actual research orchestration logic.
- Simulates Gemini and Tavily responses to make tests repeatable.
- Checks whether observed behavior matches expected behavior.
- Measures test pass rate and answer success rate.
- Estimates API-equivalent cost per successful answer.
- Produces JSON results and a Markdown report.
- Summarizes the most frequently tested failure conditions.

## How it works

```text
Evaluation cases
       |
       v
Test runner
       |
       v
Research agent
       |
       v
Mocked Gemini / Tavily responses
       |
       v
Observed result
       |
       v
Expected vs actual comparison
       |
       v
Metrics and failure analysis
       |
       v
Evaluation report
```

## Evaluation cases

The test suite includes:
- Normal research requests
- Page-fetch requests
- Empty user input
- Search API exceptions
- Search returning no results
- Invalid citations
- Page-fetch exceptions
- Empty page content
- Attempts to fetch unknown URLs

Some cases intentionally repeat the same failure mechanism using different inputs.

## Exact definition of success

A test passes when:
1. Its actual outcome matches its expected outcome.
2. Answer-expected tests return a nonempty answer and at least one source.
3. Citation validation succeeds for returned answers.
4. Tool calls stay within the configured research-step limit.
5. Error-expected tests produce the expected type of failure.

An expected error counts as a passed test, but not as a successful answer.

Test pass rate:

```text
Passed tests / Total tests × 100
```

Answer success rate:

```text
Successful answer-expected tests /
Total answer-expected tests × 100
```

## Cost per successful answer

The harness estimates token usage from the text exchanged with the mocked language model.

The calculation uses configurable input/output token prices.

```text
Estimated cost per successful answer =
Total estimated cost across all test cases /
Number of successful answers
```

Unsuccessful attempts are included in the total modeled cost.

These figures are estimates, not actual Gemini charges. The mocked test suite does not make billed Gemini or Tavily requests.

## Running locally

1. Clone this repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a local `.env` using `.env.example`.
5. Generate the evaluation cases:

```powershell
python create_test_cases.py
```

6. Run the evaluation:

```powershell
python run_evaluation.py
```

The reports will be created in the `results/` directory.

## Evaluation results

After running the suite, record the measured results here:

| Metric | Result |
|---|---|
| Total cases | 24 |
| Passed cases | 24 |
| Test pass rate | 100.0% |
| Answer success rate | 100.0% |
| Estimated cost per successful answer | $0.00020844 |

## Top three failure modes

The generated report identifies the most frequently represented adverse conditions in the test suite.

These are simulated failure scenarios, not measured production incident frequencies.

See the evaluation report for the detailed analysis.

## Limitations

- Mocked tests cannot establish real-world factual accuracy.
- Valid citation numbers do not guarantee that cited sources support every claim.
- Token counts and API-equivalent costs are estimates.
- Simulated failures do not reveal how frequently those failures occur in production.
- The current suite focuses on the research agent's orchestration and error handling.

## Technologies

- Python
- unittest.mock
- Google Gemini (target agent)
- Tavily (target agent)
- JSON
- Markdown

## Author

Sonika G.
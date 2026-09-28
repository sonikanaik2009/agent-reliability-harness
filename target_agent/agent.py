import json
import os
import re
import time
from dotenv import load_dotenv
from google import genai
from .search_tool import fetch_page, search_web

# Environment setup

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Please add it to your .env file."
    )

# Gemini client

client = genai.Client(api_key=gemini_api_key)

# Agent configuration

MAX_STEPS = 3

# Gemini helper

def ask_gemini(prompt: str):
    """
    Send a prompt to Gemini with retry handling.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
            return response.text
        except Exception as error:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise RuntimeError(
                    "The AI service is temporarily unavailable. "
                    "Please try again later."
                ) from error

# Parse agent decision

def parse_tool_decision(response_text: str):
    """
    Convert Gemini's JSON tool decision into a Python dictionary.
    """
    cleaned_response = response_text.strip()
    if cleaned_response.startswith("```"):
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        else:
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
    try:
        decision = json.loads(cleaned_response)
    except json.JSONDecodeError as error:
        raise RuntimeError("The agent returned an invalid tool decision.") from error
    if not isinstance(decision, dict):
        raise RuntimeError("The agent returned an invalid tool decision.")
    return decision

# Format sources

def format_sources(sources):
    """
    Convert collected sources into research context while preserving source provenance.
    """
    if not sources:
        return "No sources have been collected yet."
    research_context = ""
    for source in sources:
        retrieval_method = source.get("retrieval_method","search")
        research_context += f"""
Source [{source['id']}]
Title: {source['title']}
URL: {source['url']}
Retrieval method: {retrieval_method}

Content:
{source['content']}
"""
    return research_context

def validate_citations(answer, sources):
    """
    Make sure every citation number used in the answer corresponds to a real collected source.
    """
    citation_numbers = re.findall(r"\[(\d+)\]", answer)
    valid_source_ids = {
        source["id"]
        for source in sources
    }
    invalid_citations = []
    for citation in citation_numbers:
        citation_id = int(citation)
        if citation_id not in valid_source_ids:
            invalid_citations.append(citation_id)
    if invalid_citations:
        raise RuntimeError("The generated answer contained an invalid source citation.")
    return True

# Find source by URL

def find_source_by_url(sources, url):
    """
    Find an existing source using its URL.
    """
    for source in sources:
        if source["url"] == url:
            return source
    return None

# Add search results

def add_search_results(sources, search_results):
    """
    Add new search results without duplicating URLs.
    """
    existing_urls = {
        source["url"]
        for source in sources
    }
    for result in search_results:
        url = result.get("url", "")
        if not url or url in existing_urls:
            continue
        source = {
            "id": len(sources) + 1,
            "title": result.get(
                "title",
                "Untitled source"
            ),
            "url": url,
            "content": result.get(
                "content",
                ""
            ),
            "retrieval_method":"search"
        }
        sources.append(source)
        existing_urls.add(url)

# Main research agent

def research(question: str):
    """
    Research a question using an agent that can choose between web search and page fetching.
    The agent has a hard maximum number of steps so it cannot continue indefinitely.

    Returns:
        answer: Final source-grounded answer.
        sources: Sources collected by the agent.
    """
    if not question or not question.strip():
        raise ValueError("Please enter a research question.")
    sources = []
    fetched_urls = set()
    tool_history = []
    
    # Agent loop
    
    for step in range(1, MAX_STEPS + 1):
        current_sources = format_sources(sources)
        history_text = (
            "\n".join(tool_history)
            if tool_history
            else "No tools have been used yet."
        )
        decision_prompt = f"""
You are a research agent.
Research question:
{question}
You can choose between two research tools.

TOOL 1: search_web
Purpose:
Search the web and discover relevant sources.
Choose search when:
- No sources have been collected yet.
- You need additional sources.
- The existing sources do not adequately cover the question.
To use it, return:
{{
    "action": "search",
    "query": "search query"
}}

TOOL 2: fetch_page
Purpose:
Retrieve detailed content from one specific webpage that has already been discovered through search_web.
Choose fetch when:
- A known source looks useful.
- You need more detailed information from that source.
You may ONLY fetch a URL listed under Current sources.
To use it, return:
{{
    "action": "fetch",
    "url": "exact URL from Current sources"
}}

FINAL ACTION: answer
Choose answer when the collected research is sufficient to answer the question accurately.
Return:
{{
    "action": "answer"
}}

Current agent step:
{step} of {MAX_STEPS}
Current sources:
{current_sources}
Previous tool activity:
{history_text}

Important rules:
- Return ONLY valid JSON.
- Do not include Markdown.
- Do not include explanations outside the JSON.
- Never invent a URL.
- Only fetch URLs listed in Current sources.
- Do not repeatedly fetch the same URL.
- Do not repeat the same search unnecessarily.
- If no sources exist yet, choose search.
- If sufficient research has been collected, choose answer.
"""
        decision_text = ask_gemini(decision_prompt)
        decision = parse_tool_decision(decision_text)
        action = decision.get("action", "").lower()
        
        # Agent selected SEARCH

        if action == "search":
            search_query = decision.get(
                "query",
                ""
            ).strip()
            if not search_query:
                search_query = question
            try:
                search_results = search_web(search_query)
            except Exception as error:
                tool_history.append(f"Step {step}: search_web failed.")
                continue
            if not search_results:
                tool_history.append(
                    f"Step {step}: search_web returned "
                    f"no results for '{search_query}'."
                )
                continue
            old_source_count = len(sources)
            add_search_results(sources,search_results)
            new_source_count = (len(sources) - old_source_count)
            tool_history.append(
                f"Step {step}: search_web "
                f"searched for '{search_query}' "
                f"and added {new_source_count} "
                f"new sources."
            )

        # Agent selected FETCH

        elif action == "fetch":
            selected_url = decision.get(
                "url",
                ""
            ).strip()
            source = find_source_by_url(sources, selected_url)
            if source is None:
                tool_history.append(
                    f"Step {step}: fetch_page was not "
                    f"executed because the selected URL "
                    f"was not a known source."
                )
                continue
            if selected_url in fetched_urls:
                tool_history.append(
                    f"Step {step}: fetch_page was not "
                    f"executed because this source had "
                    f"already been fetched."
                )
                continue
            try:
                page_content = fetch_page(selected_url)
            except Exception:
                tool_history.append(
                    f"Step {step}: fetch_page failed "
                    f"for Source [{source['id']}]."
                )
                continue
            if not page_content:
                tool_history.append(
                    f"Step {step}: fetch_page returned "
                    f"no content for "
                    f"Source [{source['id']}]."
                )
                continue
            source["content"] = page_content
            source["retrieval_method"]="page_fetch"
            fetched_urls.add(selected_url)
            tool_history.append(
                f"Step {step}: fetch_page retrieved "
                f"detailed content for "
                f"Source [{source['id']}]."
            )

        # Agent selected ANSWER

        elif action == "answer":
            break

        # Invalid action

        else:
            tool_history.append(
                f"Step {step}: The agent requested "
                f"an invalid action."
            )
            continue
    
    # Make sure research exists

    if not sources:
        raise RuntimeError("The research agent could not find any usable web sources.")

    # Generate final answer

    final_sources = format_sources(sources)
    final_prompt = f"""
You are a source-grounded research assistant.
Answer the user's research question using ONLY the research sources provided below.
Research question:
{question}
Research sources:
{final_sources}

STRICT SOURCE AND CITATION RULES:
1. Every factual claim in the answer must be supported by at least one of the provided sources.

2. Place the supporting source number immediately after the factual claim.

3. Use citations only in this format: [1], [2], [3], etc.

4. If multiple sources support the same claim, use: [1][2]

5. A citation number must refer to the source with the same Source ID shown in the research context.

6. Never cite a source unless its provided content actually supports the claim.

7. Never create or invent source numbers.

8. Never create or invent URLs.

9. Do not use outside knowledge, even if you know the answer independently.

10. If the provided sources do not support a factual claim, omit that claim.

11. If the available research is insufficient to answer part of the question, explicitly state that the available sources do not provide enough information.

12. Keep citations attached to the claims they support.

Give a clear and well-structured final answer.
"""
    answer = ask_gemini(final_prompt)
    validate_citations(answer, sources)
    return answer, sources
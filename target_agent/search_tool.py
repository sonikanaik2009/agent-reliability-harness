import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Environment setup 

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError(
        "TAVILY_API_KEY was not found. "
        "Please add it to your .env file."
    )

# Tavily Client

tavily_client = TavilyClient(api_key=tavily_api_key)

# Tool 1: Web Search 
def search_web(query: str, max_results: int = 5):
    """
    Search the web for relevant sources.
    Args:
        query: The search query.
        max_results: Maximum number of results to return.
    Returns: A list of sources containing title, URL, and content.
    """
    if not query or not query.strip():
        return []
    response = tavily_client.search(query=query, search_depth="basic", max_results=max_results)
    sources = []
    for index, result in enumerate(response.get("results", []),start=1):
        source={
            "id": index,
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("content")
        }
        sources.append(source)
    return sources

# Tool 2: Page Fetch

def fetch_page(url:str):
    """
    Fetch detailed content from a specific webpage.
    Args:
        url: URL of the webpage to retrieve.
    Returns:
        Extracted webpage content as text.
    """
    if not url or not url.strip():
        return ""
    response = tavily_client.extract(urls = [url])
    results = response.get("results", [])
    if not results:
        return ""
    content = results[0].get("raw_content", "")
    return content or "" 
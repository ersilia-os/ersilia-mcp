"""Fetch and format the Ersilia model hub catalog."""

from urllib.parse import urljoin

import requests

from ersilia_mcp.utils.logging import logger

ERSILIA_SEARCH_API_BASE_URI = "https://search-engine-six-iota.vercel.app"


def format_search_results(results: list) -> list:
    """Format search API results as compact lines.

    Parameters
    ----------
    results : list
        Search results from the API (list of dicts).

    Returns
    -------
    list
        Formatted lines with identifier, slug, title, score, and matched keywords.
    """
    lines = []
    for result in results:
        identifier = result.get("Identifier")
        slug = result.get("Slug")
        if not identifier or not slug:
            continue
        title = result.get("Title", "")
        score = result.get("score", "")
        matched = result.get("matched_keywords", "")
        line = f"{identifier}  {slug} — {title}"
        if score:
            line += f" (score: {score}"
            if matched:
                line += f", matched: {matched}"
            line += ")"
        lines.append(line)
    return lines


def search_catalog(query: str) -> str:
    """Search the Ersilia model hub by keyword via the search API.

    Parameters
    ----------
    query : str
        Search query (e.g. "malaria", "toxicity").

    Returns
    -------
    str
        One ``identifier  slug — title`` line per result, plus score and
        matched keywords, or a message on error.
    """
    try:
        url = urljoin(ERSILIA_SEARCH_API_BASE_URI, "/search")
        params = {"text": query, "all_statuses": False, "limit": 50}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        count = data.get("count", 0)
        if count == 0:
            logger.info("No results found for query '%s'", query)
            return f"No results found for query '{query}'."
        results = data.get("results", [])
        lines = format_search_results(results)
        logger.success("Found %d results for query '%s'", len(lines), query)
        return "\n".join(lines) or f"No results found for query '{query}'."
    except requests.RequestException as exc:
        logger.error("Search API request failed: %s", exc)
        return f"Search API request failed: {exc}"
    except Exception as exc:
        logger.error("Failed to search catalog: %s", exc)
        return f"Failed to search catalog: {exc}"

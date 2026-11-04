"""Fetch and format the Ersilia model hub catalog."""

from urllib.parse import urljoin

import requests

from ersilia_mcp.utils.logging import logger

ERSILIA_SEARCH_API_BASE_URI = "https://search-engine-six-iota.vercel.app"

# Each result line costs the client tokens, so return few by default.
DEFAULT_LIMIT = 10
MAX_LIMIT = 50


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


def search_catalog(query: str, limit: int = DEFAULT_LIMIT) -> str:
    """Search the Ersilia model hub by keyword via the search API.

    Parameters
    ----------
    query : str
        Search query (e.g. "malaria", "toxicity").
    limit : int, default=10
        Maximum number of results to return (clamped to 1-50).

    Returns
    -------
    str
        One ``identifier  slug — title`` line per result, plus score and
        matched keywords, a final note when more matches exist than were
        returned, or a message on error.
    """
    limit = max(1, min(limit, MAX_LIMIT))
    try:
        url = urljoin(ERSILIA_SEARCH_API_BASE_URI, "/search")
        params = {"text": query, "all_statuses": False, "limit": limit}
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
        if not lines:
            return f"No results found for query '{query}'."
        if count > len(lines):
            lines.append(
                f"Showing {len(lines)} of {count} matches; refine the query "
                "or raise limit to see more."
            )
        return "\n".join(lines)
    except requests.RequestException as exc:
        logger.error("Search API request failed: %s", exc)
        return f"Search API request failed: {exc}"
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to search catalog: %s", exc)
        return f"Failed to search catalog: {exc}"

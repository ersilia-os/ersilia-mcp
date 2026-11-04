"""The ``search_model`` tool."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.search_api import search_catalog


def register(mcp: FastMCP) -> None:
    """Register the search tool on the MCP server."""

    @mcp.tool(timeout=30.0)
    async def search_model(query: str, limit: int = 10) -> str:
        """Search the Ersilia model hub by keyword.

        Parameters
        ----------
        query : str
            Search query (e.g. "malaria", "toxicity").
        limit : int, optional
            Maximum number of results (default 10, at most 50).

        Returns
        -------
        str
            One ``identifier  slug — title`` line per result, plus score and
            matched keywords, or a message on error.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, search_catalog, query, limit)

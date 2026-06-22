"""The ``search_model`` tool."""

from mcp.server.fastmcp import FastMCP

from ersilia_mcp.utils.search_api import search_catalog


def register(mcp: FastMCP) -> None:
    """Register the search tool on the MCP server."""

    @mcp.tool()
    def search_model(query: str) -> str:
        """Search the Ersilia model hub by keyword.

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
        return search_catalog(query)

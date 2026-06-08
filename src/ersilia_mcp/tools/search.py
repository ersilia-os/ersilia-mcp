"""The ``search_model`` tool."""

from mcp.server.fastmcp import FastMCP

from ersilia_mcp.catalog import fetch_catalog


def register(mcp: FastMCP) -> None:
    """Register the search tool on the MCP server."""

    @mcp.tool()
    def search_model() -> str:
        """Search the Ersilia model hub catalog.

        Returns
        -------
        str
            One ``identifier  slug — title`` line per model, or a message on
            error.
        """
        return fetch_catalog()

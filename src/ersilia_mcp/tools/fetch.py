"""MCP tools for fetching Ersilia models and seeing if the model is fetched"""

from mcp.server.fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    fetch_model_helper,
)


def register(mcp: FastMCP) -> None:
    """Register the model tools on the MCP server."""

    @mcp.tool()
    def fetch_model(model: str) -> bool:
        """Fetch a model from the Ersilia model hub.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        bool
            True if fetched, False otherwise.
        """
        return fetch_model_helper(model)

    @mcp.tool()
    def check_model_fetched(model: str) -> bool:
        """Check if a model is fetched from the Ersilia model hub.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        bool
            True if fetched, False otherwise.
        """
        return check_model_fetched_helper(model)

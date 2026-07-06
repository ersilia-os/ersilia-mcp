"""MCP tools for fetching Ersilia models and seeing if the model is fetched"""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    fetch_model_helper,
)


def register(mcp: FastMCP) -> None:
    """Register the model tools on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def fetch_model(model: str) -> bool:
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
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, fetch_model_helper, model)

    @mcp.tool(timeout=10.0)
    async def check_model_fetched(model: str) -> bool:
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
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, check_model_fetched_helper, model)
